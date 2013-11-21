define(['underscore', 'text!deleteModalTemplate',
        'text!feedbackTemplate', 'text!changePasswordTemplate',
        'text!passwordChangeStatusModalTemplate', 
        'text!downloadJobTemplate', 'text!createJobTemplate'], 
		function (_, deleteModalTemplate, feedbackTemplate, changePasswordTemplate,
				passwordChangeStatusModalTemplate, 
				downloadJobTemplate, createJobTemplate) {	
			"use strict";
			var controller=['$scope','Restangular','$timeout','$modal','$location',
			                '$rootScope','$log',
				/* 
				 * This "base" controller provides some default scope components for all the
				 * other controllers.  It also handles the auto-reloading of things like jobs 
				 * in progress and uploads, etc. 
				 */
				function NMTKCtrl($scope, Restangular, $timeout, $modal, $location,
								  $rootScope, $log) {	
					// A Function used to update data via a rest call to an API interface,
					// since it seems like we will refresh far more often than we don't, might
					// as well do this.
				
					$scope.csrftoken=CONFIG.csrftoken;
					$scope.browser_name=BrowserDetect.browser;
					$scope.browser_version=BrowserDetect.version;
					$scope.loaded=false;
					$log.info('Using', $scope.browser_name, $scope.browser_version);
					$scope.refreshItems=[];
					$scope.tabs={};
					$rootScope.rest={};
					$rootScope.restargs={};
					$rootScope.resources={};
					$scope.delete_candidate={};
					$scope.job_config=undefined;
					$scope.results_job=undefined;
					$scope.views={}
					$scope.switchView=function(view) {
						$scope.views[view]=!$scope.views[view];
					}
					
					$scope.toggleDiv=function(div) {
						if (_.indexOf($scope.preferences.divs, div) > -1) {
							$scope.preferences.divs=_.without($scope.preferences.divs, div);
						} else {
							$scope.preferences.divs.push(div);
						}
						
						var copy=Restangular.copy($scope.preferences);
						copy.divs=JSON.stringify($scope.preferences.divs);
						copy.put();
					}
					
					// Check to see if a div is enabled and return a true/false response.
					$scope.isDivEnabled=function(div) {
						// Preferences loaded yet?
						if (typeof $scope.preferences === 'undefined') {
							return true;
						}
						return _.indexOf($scope.preferences.divs, div) > -1;
					}
					
					$rootScope.refreshData=function (api, offset) {
						if (typeof $rootScope.restargs[api] === 'undefined') {
							$rootScope.restargs[api]={};
						}
						if (typeof offset !== 'undefined') {
							$rootScope.restargs[api]['offset']=offset;
						} 
						var rest=$rootScope.resources[api];
						$rootScope.rest[api]=rest.getList($rootScope.restargs[api]);
					};
					
					// When OK is pressed on the modal confirm dialog, delete the
					// requested data
					$scope.cancelDeleteData=function () {
						$scope.delete_candidate={};
					}
					
					$rootScope.deleteData=function (api, id) {
						var rest=$rootScope.resources[api];
						rest.one(id).remove().then(function (r) {
							$rootScope.refreshData(api);
						}, function (r) {
							alert('Please delete jobs for this file prior to deleting the file.')
						});
					}
					
					$scope.removeFile=function (api, id, name, type) {
						var modal_dialog=$modal.open({
							controller: 'DeleteCtrl',
							resolve: {api: function () { return api; },
								      id: function () { return id; },
								      name: function () { return name; },
								      type: function () { return type; },},
							template: deleteModalTemplate
						});
						modal_dialog.result.then(function (result) {
							$scope.deleteData(result[0], result[1]);
						});
					}
					
					$scope.changePassword=function() {
						$rootScope.rest['user']=$rootScope.resources['user'].getList();
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
					
					_.each(['datafile','tool','job'], function (item) {
						$rootScope.resources[item]=Restangular.all(item);
						$scope.refreshData(item);
					});
					$rootScope.resources['feedback']=Restangular.all('feedback');
					$rootScope.resources['user']=Restangular.all('user');
					$rootScope.active={'job': undefined,
							           'tool': undefined,
							           'datafile': undefined,}
					/* 
					 * Load user preferences for the UI
					 */
					$rootScope.resources['preference']=Restangular.all('preference');
					// The app ensures that all users have a preference record by default.
					$rootScope.resources['preference'].getList().then(function (data) {
						if (data.length) {
							/*
							 * The preference field divs has a list of divs that should
							 * be enabled in the UI.
							 */
							$scope.preferences=data[0];
							$scope.preferences.divs=JSON.parse($scope.preferences.divs);
						} 
					});
					
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
						var rest=$rootScope.resources['feedback'];
						$rootScope.rest['feedback']=rest.getList({'uri': $location.path(),
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
					
					$scope.setConfigureJob=function (working_job_id) {
						$scope.working_job_id=working_job_id;
					}
					
					$scope.configureJob=function (job) {
						if ($scope.working_job_id && $scope.working_job_id != job.job_id) {
							var modal_dialog=$modal.open({templateUrl:  'switchjob.html', 
														  controller: 'SwitchJobCtrl'});
							modal_dialog.result.then(function () {
								$scope.job_config=undefined;
								$scope.errors=undefined;
								$scope.working_job_id=job.id;
								$location.path('/job/' + $scope.working_job_id + '/');
							});
						} else {
							$scope.working_job_id=job.id;
							$location.path('/job/' + $scope.working_job_id + '/');
						}
					};
					
					$scope.downloadJob=function (job) {
						var d=$modal.open({ template:  downloadJobTemplate, 
											controller: 'DownloadJobCtrl',
											resolve:{ job: function () { return job; } },
											scope: $scope
										  });
					}
					
					$scope.createJob=function (tool_uri) {
						var modal_instance=$modal.open({scope: $scope,
														backdrop: true,
														resolve: {'tool': function () { return tool_uri; }},
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
					};
					
				}
	];
	return controller;
});
