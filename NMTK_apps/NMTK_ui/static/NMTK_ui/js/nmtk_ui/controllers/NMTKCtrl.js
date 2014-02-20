define(['underscore'
        , 'text!deleteModalTemplate'
        , 'text!feedbackTemplate'
        , 'text!changePasswordTemplate'
        , 'text!passwordChangeStatusModalTemplate'
        , 'text!switchJobModalTemplate'
        , 'text!downloadDatafileTemplate'
        , 'text!createJobTemplate'
        , 'text!loginTemplate'], 
		function (_, deleteModalTemplate, feedbackTemplate, changePasswordTemplate,
				passwordChangeStatusModalTemplate, switchJobModalTemplate,
				downloadDatafileTemplate, createJobTemplate, loginTemplate) {	
			"use strict";
			var controller=['$scope','Restangular','$timeout','$modal','$location',
			                '$http','$q', '$log',
				/* 
				 * This "base" controller provides some default scope components for all the
				 * other controllers.  It also handles the auto-reloading of things like jobs 
				 * in progress and uploads, etc. 
				 */
				function ($scope, Restangular, $timeout, $modal, $location, 
						  $http, $q, $log) {
					// A Function used to update data via a rest call to an API interface,
					// since it seems like we will refresh far more often than we don't, might
					// as well do this.
					$log.info('NMTK Controller running!');
					$scope.csrftoken=CONFIG.csrftoken;
					$scope.login_url=CONFIG.api_path + 'user/login/';
					$scope.register_url=CONFIG.register_url;
					$scope.reset_url=CONFIG.reset_url;
					$scope.browser_name=BrowserDetect.browser;
					$scope.browser_version=BrowserDetect.version;
					$scope.loaded=false;
					$log.info('Using', $scope.browser_name, $scope.browser_version);
					$scope.refreshItems=[];
					$scope.tabs={};
					/*
					 * Restargs are argument passed in to each request for an 
					 * API component.
					 * $scope.resources is a list of core resources - used for
					 * retrieving and updating stuff.
					 * $scope.rest is an object containing promises - we can use
					 * these with .then() anywhere to refresh data when the promise
					 * gets refreshed/updated later.
					 */
					$scope.restargs={};
					$scope.resources={};
					$scope.rest={};
					$scope.delete_candidate={};
					$scope.job_config=undefined;
					$scope.preview_datafile=undefined;
					$scope.views={}
					$scope.switchView=function(view) {
						$scope.views[view]=!$scope.views[view];
					}
					$scope.user={};
					$scope.toggleDiv=function(div) {
						if (_.indexOf($scope.preferences.divs, div) > -1) {
							$scope.preferences.divs=_.without($scope.preferences.divs, div);
						} else {
							$scope.preferences.divs.push(div);
						}
						if ($scope.logged_in) {
							var copy=Restangular.copy($scope.preferences);
							copy.divs=JSON.stringify($scope.preferences.divs);
							copy.put();
						}
					}
					
					// Check to see if a div is enabled and return a true/false response.
					$scope.isDivEnabled=function(div) {
						// Preferences loaded yet?
						if (typeof $scope.preferences === 'undefined') {
							return true;
						}
						return _.indexOf($scope.preferences.divs, div) == -1;
					}
					/*
					 * A simple function that returns an empty list as it's
					 * promise result.  This "fakes out" things like datafile
					 * which doesn't actually resolve when the user isn't logged
					 * in.
					 */
					$scope.emptyPromise=function () {
						var deferred=$q.defer();
						deferred.resolve([]);
						return deferred.promise
					}
					
					$scope.refreshData=function (api, offset) {
						if (typeof $scope.restargs[api] === 'undefined') {
							$scope.restargs[api]={};
						}
						if (typeof offset !== 'undefined') {
							$scope.restargs[api]['offset']=offset;
						} 
						var rest=$scope.resources[api];
						/*
						 * If the user isn't logged in, only the user and
						 * tool data should be queried.
						 */
						if (($scope.logged_in == true) ||
						    (_.indexOf(['user','tool'], api) > -1)) {
							$scope.rest[api]=rest.getList($scope.restargs[api]);
						} else {
							$scope.rest[api]=$scope.emptyPromise()
						}
						/*
						 * If the preference data updates, then we need to ensure that
						 * we process the updated data.
						 * 
						 */
						if (api == 'preference') {
							$scope.rest[api].then(function (data) {
								if (data.length) {
									/*
									 * The preference field divs has a list of divs that should
									 * be collapsed in the UI.
									 */
									$scope.preferences=data[0];
									$scope.preferences.divs=JSON.parse($scope.preferences.divs);
								} 
							});
						} else if (api == 'user') {
							$scope.rest[api].then(function (data) {
								/* 
								 * Only update the user information if the URI of
								 * the user changes (so we don't bother to look at 
								 * things like last login for the refresh.)
								 */
								$scope.logged_in=true;
								$scope.$broadcast('login', true);
								if ($scope.user.resource_uri != data[0].resource_uri) {
									$scope.user=data[0];
									$scope.refreshAllData();
								}
							}, function (error) {
								/*
								 * Here the user is logged out/not logged in.  In such
								 * cases we need to clear all the resources we have and
								 * just refresh the user information (in case login in
								 * another tab/window happens.)
								 */
								if (error.status == 401) {
									$scope.logged_in=false;
									$scope.user={};
									$scope.refreshAllData();
									$scope.preferences={'divs': [] };
								}
							});
						} else {
							$scope.rest[api].then(null, function (error) {
								if (error.status == 401) {
									if ($scope.user.is_active) {
										$scope.refreshData('user');
									}
								}
							})
						}
					};
					
					// When OK is pressed on the modal confirm dialog, delete the
					// requested data
					$scope.cancelDeleteData=function () {
						$scope.delete_candidate={};
					}
					
					$scope.deleteData=function (api, id) {
						var rest=$scope.resources[api];
						rest.one(id).remove().then(function (r) {
							$scope.refreshData(api);
						}, function (r) {
							alert('Please delete jobs for this file prior to deleting the file.')
						});
					}
					$scope.loginCheck=function () {
						if (! $scope.user.is_active ) {
							var path=$location.path();
							$location.path('/');
							$log.info('Running logincheck w/redirect to', path);
							$scope.login({'redirect': path});
						}
					}

					$scope.$watch('user', function () {
						$scope.loginCheck();
					});
					
					$scope.removeFile=function (api, item, name, type, operation) {
						if ((typeof(operation) === 'undefined') || (! operation) ) {
							operation='Delete';
						}
						var files=null;
						if (api == 'datafile') {
							files=function (id) {
								return $q.all([
									Restangular.all('job_file').getList({'datafile': item.id,
							                                  		     'limit': 999}),
									Restangular.all('job_results').getList({'datafile': item.id,
                       		           										'limit': 999})
                   		    ])}();
						} 
						var modal_dialog=$modal.open({
							controller: 'DeleteCtrl',
							resolve: {api: function () { return api; },
								      id: function () { return item.id; },
								      name: function () { return name; },
								      operation: function () { return operation; },
								      type: function () { return type; },
								      files: function () { return files; },
								      jobdata: function () { return $scope.rest['job']}},
							template: deleteModalTemplate
						});
						modal_dialog.result.then(function (result) {
							$scope.deleteData(result[0], result[1]);
						});
					}
					
					$scope.changePassword=function() {
						$scope.rest['user']=$scope.resources['user'].getList();
						var modal_dialog=$modal.open({
							controller: 'ChangePasswordCtrl',
							template: changePasswordTemplate
						});
						modal_dialog.result.then(function (password) {
							var modal_dialog=$modal.open({
								controller: ['$scope','$modalInstance',
								             function ($scope, $modalInstance) {
												$scope.close=function () { $modalInstance.dismiss(); };
											 }
											],
								template: passwordChangeStatusModalTemplate,
								scope: $scope
							});
							$scope.rest['user'].then(function (data) {
								var user_info=data[0];
								user_info['password']=password.password;
								user_info['old_password']=password.old_password;
								user_info.put().then(function () {
									$scope.message='Password changed successfully.';
									$scope.result='Complete';
								}, function (result) {
									$scope.result='Failed';
									$scope.message=result.data.user.__all__;
								})
							})
						});
					}
					
					$scope.changeTab=function(newtab) {
						$log.info('Got request to change to', newtab);
						$scope.activeTab=newtab;
					}
					$scope.toggleTab=function(tabName){
						$scope.tabs[tabName]=!$scope.tabs[tabName];
					};
					
					// Enable the auto-refresh of API elements using a timer.
					$scope.enableRefresh=function (items) {
						$scope.refreshItems=items
					}
					
					/*
					 * Log out the currently logged in user.
					 */
					$scope.resources['user']=Restangular.all('user');
					$scope.refreshData('user');
					$scope.logout= function () {
						$http({method: 'GET',
							   url: $scope.user.logout,
							   headers: {'X-CSRFToken': $scope.csrftoken }
						}).success(function (data, status, headers, config) {
							$scope.refreshData('user');
						});
					}
					
					/*
					 * Watch the user variable, if it changes, we need to
					 * be sure to refresh all our stuff.
					 * In here is all the code that is used when a login event
					 * occurs
					 */
					$scope.refreshAllData=function () {
						_.each(['datafile','job', 'preference','tool'], function (item) {
							$scope.resources[item]=Restangular.all(item);
							$scope.refreshData(item);
						});
					}
										
					$scope.refreshAllData();					
					
					$scope.active={'job': undefined,
							       'tool': undefined,
							       'datafile': undefined,}
					
					
					$scope.updateData= function (model, offset) {
						$log.info('Updatedata arguments', model, offset);
						$scope.refreshData(model, offset);
					}
					$scope.timeout=15000;
					// Refresh the models in the refresh list every 30s.
					$scope.timedRefresh=function () {
						_.each($scope.refreshItems, function (item) { 
							$scope.refreshData(item);
						});
						$timeout($scope.timedRefresh, $scope.timeout);
					}
					$scope.timedRefresh();
				//	Restangular.all('tool').getList().then(function (data) { $log.info(data);});
					
					window.uploadDone=function(){
						if ($scope.loaded) {
						  /* have access to $scope here*/
						    $log.info('Upload complete detected!');
						    $timeout(function () {$scope.refreshData('datafile');}, 1000)
						}
						$scope.loaded=true;
						$("#ie_uploadform").trigger('reset');
					}
					
					$scope.feedback=function () {
						$scope.resources['feedback']=Restangular.all('feedback');
						var rest=$scope.resources['feedback'];
						$scope.rest['feedback']=rest.getList({'uri': $location.path(),
							                                  'limit': 1}).then(function(result) {
							if (result.length) {
								$scope.record=result[0];
							} else {
								$scope.record={};
							}
										
							var modal_instance=$modal.open({template: feedbackTemplate,
									     				    scope: $scope,
									     				    controller: 'FeedbackCtrl',
									     				    backdrop: true});
							modal_instance.result.then(function (result) {
								if (result) {
									$log.info('Got a feedback response!', result);
									result.uri=$location.path();
									rest.post(result);
								}
							});
						});
					}
					$scope.login_displayed=false;
					$scope.login=function (options) {
						if (! $scope.login_displayed) {
							$scope.login_displayed=true;
							var modal_instance=$modal.open({template: loginTemplate,
									     				    scope: $scope,
									     				    controller: 'LoginCtrl',
									     				    backdrop: true});
							
							modal_instance.result.then(function (result) {
								$scope.login_displayed=false;
								$scope.refreshData('user');
								$scope.rest['user'].then(function (data) {
									if (typeof options !== 'undefined') {
										if (typeof options.redirect !== 'undefined') {
											$location.path(options.redirect);
										} else if (typeof options.post_func !== 'undefined') {
											options.post_func();
										}
									}
								});
							}, function (err) {
								$scope.login_displayed=false;
							});
						}
						
					}
					
					$scope.setConfigureJob=function (working_job_id) {
						$scope.working_job_id=working_job_id;
					}
					
					$scope.configureJob=function (job) {
						if ($scope.working_job_id && $scope.working_job_id != job.job_id) {
							var modal_dialog=$modal.open({template:  switchJobModalTemplate, 
														  controller: 'SwitchJobCtrl'});
							modal_dialog.result.then(function () {
								$scope.job_config=undefined;
								$scope.job_config_file=undefined;
								$scope.errors=undefined;
								$scope.working_job_id=job.id;
								$location.path('/job/' + $scope.working_job_id + '/');
							});
						} else {
							$scope.working_job_id=job.id;
							$location.path('/job/' + $scope.working_job_id + '/');
						}
					};
					
					/*
					 * This little section of code handles returning to a previous
					 * route, if one exists.
					 */
					var history = [];

				    $scope.$on('$routeChangeSuccess', function() {
				        history.push($location.$$path);
				    });

				    $scope.back = function () {
				        var prevUrl = history.length > 1 ? history.splice(-2)[0] : "/";
				        if (prevUrl) {
				        	$location.path(prevUrl);
				        } else {
				        	$location.path('/');
				        }
				    };
					
				    
					$scope.downloadDatafile=function (datafile, job) {
						if (! datafile) {
							/*
							 * If we are given a job, we need to return a promise
							 * that gives back a single datafile object
							 */
							var primary_result=_.find(job.results_files, function (rf) {
								return rf.primary;
							});
							if (typeof primary_result !== 'undefined') {
								var datafile_func=function () {
									var deferred=$q.defer();
									$scope.rest['datafile'].then(function (datafiles) {
										var this_df=_.find(datafiles, function (df) {
											return (df.resource_uri == primary_result.datafile);
										});
										deferred.resolve(this_df);
									})
									return deferred.promise;
								}
								datafile=datafile_func();
							} else {
								$log.error('No primary result for this job?!?');
							}
							
						} 
						var d=$modal.open({ template:  downloadDatafileTemplate, 
											controller: 'DownloadDatafileCtrl',
											resolve:{ datafile: function () { return datafile; } },
											scope: $scope
										  });
					}
					$scope.getFileStr=function (o) {
						if (o.description) {
							return o.name + ' (' + o.description + ')';
						} else {
							return o.name;
						}
					}
					$scope.createJob=function (tool_uri, data_file_uri) {
						if (! $scope.user.is_active) {
							$scope.login({'post_func': function () { $scope.createJob(tool_uri, data_file_uri) }});
						} else {
							var modal_instance=$modal.open({scope: $scope,
															backdrop: true,
															resolve: {'tool': function () { return tool_uri; },
																      'data_file': function () { return data_file_uri; }},
															template:  createJobTemplate, // OR: templateUrl: 'path/to/view.html',
															controller: 'CreateJobCtrl'});
							modal_instance.result.then(function(result) {
								$scope.resources['job'].post(result).then(function (api_result) {
									$scope.refreshData('job');
									$scope.rest['job'].then(function () {
										$location.path('/job/' +
													   api_result.resource_uri.split('/').reverse()[1] + '/');
									});
								});			
							});
							$log.info('Creating a new job!');
						}
					};
				}
			];
			return controller;
	}
);
