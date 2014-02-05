define(['underscore',
        'text!configureErrorsTemplate',
        'text!cloneConfigTemplate'], function (_, configureErrorsTemplate,
        		cloneConfigTemplate) {	
	"use strict";
	var controller=['$scope', '$routeParams', '$location', '$modal', '$log',
		/*
		 * Output the form that is used to configure a job, and take the resulting 
		 * data to send up to the server so the job configuration can be validated.
		 * 
		 * Once a response comes back, we'll have to check for errors and then set
		 * the appropriate error messages in the template as well...
		 */
		function ($scope, $routeParams, $location, $modal, $log) {
			$scope.loginCheck();
			var jobid=$routeParams.jobid;
			$scope.$parent.job_uri=$location.path();
			// Get Job, tool, and file information, then use them to generate the form
			// configuration.
			$scope.tool_config=[];
			
			$log.info('Job config is ', $scope.$parent.job_config);
			
			$scope.sections={}
			$scope.toggleSection=function (type) {
				$scope.sections[type]=!$scope.sections[type];
			}
			$scope.rest.job.then(function (jobs) {
				var job_data=undefined;
				_.each(jobs, function (job) {
					if (job.id == jobid) {
						job_data=job;
					}
				}); 
				$scope.job_data=job_data;
				var tool_id=job_data.tool.split('/').reverse()[1];
				if (job_data.data_file) {
					var file_id=job_data.data_file.split('/').reverse()[1];
				} else {
					var file_id=null;
				}
				$scope.disabled=(job_data.status != 'Configuration Pending');
				$log.info('Setting is ', $scope.disabled);
				$scope.rest.tool.then(function (row) {
					var tool_data=undefined;
					_.each(row, function(toolinfo) {
						if (toolinfo.id==tool_id) {
							tool_data=toolinfo;
						}
					});
					$log.info('Got tool data of ', tool_data);
					/*
					 * Go through and setup the default state of the different 
					 * sections here.
					 */
					var i=0;
					_.each(tool_data.config.input, function (data) {
						if (_.has(data,'expanded')) {
							$scope.sections['input:' + i]=data.expanded;
						} else if (data.type == 'File' && _.has(data, 'primary') && data.primary) {
							$scope.sections['input:'+i]=true;
						} else {
							$scope.sections['input:'+i]=false
						}
						i+=1;
					});
					_.each(tool_data.config.output, function (data) {
						if (_.has(data,'expanded')) {
							$scope.sections['output:' + i]=data.expanded;
						} else if (data.type == 'File' && _.has(data, 'primary') && data.primary) {
							$scope.sections['output:'+i]=true;
						} else {
							$scope.sections['output:'+i]=false
						}
						i+=1;
					});
					// If we don't have a config, we'll build a default using
					// the tool information
					if (! $scope.$parent.job_config) {
						$scope.$parent.job_config={};
						_.each(['input','output'], function (section) {
							_.each(tool_data.config[section], function (data) {
								_.each(data.elements, function (config_set) {
									if (_.has(config_set, 'default')) {
										$scope.$parent.job_config[data.namespace + ":" + config_set.name]=config_set.default;
									} else if (data.type == 'File' && data.primary) {
										// If it is from a file, we'll try to default things to the
										// field in the file that matches the name in the tool config.
										$scope.$parent.job_config[data.namespace + ":" + config_set.name]=config_set.name;
									}
								});
							});
						});
					}
					$log.info('Config is', $scope.$parent.job_config);
					$scope.tool_name=tool_data.name;
					$scope.tool_data=tool_data;
//					/*
//					 * regardless of whether a file is required, we'll do this
//					 * for the sake of simplicity.  The file list ought to already
//					 * be loaded anyways, so it's only the cost of doing this 
//					 * async...
//					 */
//					$scope.rest.datafile.then(function (files) {
//						var file_data=undefined;
//						_.each(files, function (data) {
//							if (data.id == file_id) {
//								file_data=data;
//							}
//						});
//						// Compute a list of fields to select from for property selection
//						// dialogs
//						if (file_id) {
//							$scope.file_name=file_data.name;
//							$scope.fields=[]
//							_.each(JSON.parse(file_data.fields), function (v) {
//								$scope.fields.push({'label': v,
//									         		'value': v});
//							});
//						}
//						
//					});
				});
			});
			$scope.file_fields={};
			$scope.setConfigureJob(jobid);
			$scope.enableRefresh([]);
			$scope.changeTab('configurejob');
			$scope.closeConfig=function () {
				$scope.$parent.job_uri=null;
				$scope.$parent.job_config={};
				$location.path('/job');
			}
			$scope.rest.datafile.then(function (datafiles) {
				$scope.updateFileFieldsFromResourceURI=function (key) {
					var resource_uri=$scope.$parent.job_config[key];
					if (typeof resource_uri !== 'undefined') {
						$log.info('Resource URI is ', resource_uri);
						
						var df=_.find(datafiles, function (datafile) {
							return (datafile.resource_uri == resource_uri);
						});
						
						var fields=[];
						_.each(JSON.parse(df.fields), function (v) {
							fields.push({'label': v,
								         'value': v});
						});
						$scope.file_fields[key]=fields;
						$log.info('Data file fields are ', $scope.file_fields);
					} else {
						$scope.file_fields[key]=[];
					}
				}
			});
			
			$scope.rest.datafile.then(function(data_files) {
				$scope.list_files=function (types) {
					var files=[];
					if (typeof types !== 'undefined') {
						_.each(data_files, function (file_entry) {
							if (_.contains(types,file_entry.content_type)) {
								files.push(file_entry);
							}
						});
						
					} else {
						_.each(data_files, function (file_entry) {
							if (/complete/i.exec(file_entry.status)) {
								$log.info(file_entry.name)
								files.push(file_entry);
							}
						});
					}
					return files;
				};
			});
			
			$scope.submit_job=function () {
				$scope.resources['job'].getList({'job_id': $scope.job_data.id}).then(function (response) {
					var data=response[0];
					data.config=$scope.$parent.job_config;
					data.put().then(function (response) {
						$log.info(response);
						// Return them to the job window.
						$scope.closeConfig();
					}, function (response) {
						/* Function called when an error is returned */
						$scope.$parent.errors=response.data.job.config;
						var opts = {
							    backdrop: true,
							    keyboard: true,
							    backdropClick: true,
							    template: configureErrorsTemplate, // OR: templateUrl: 'path/to/view.html',
							    controller: ['$scope','dialog', function ($scope, dialog) {
												$scope.messages=dialog.options.errors;
												$scope.close=function () {
													dialog.close();
												}
											}]
							  };
						opts.errors=$scope.$parent.errors;
						var d=$modal.dialog(opts);
						d.open();
					});
				});
			}
		
			
			$scope.cloneConfig=function (target_namespace) {
				var modal_dialog=$modal.open({
					backdrop: true,
					scope: $scope,
				    template:  cloneConfigTemplate, // OR: templateUrl: 'path/to/view.html',
				    controller: 'CloneConfigCtrl'
				});
				modal_dialog.result.then(function (job_config) {
					var other_config=JSON.parse(job_config);
					$log.info('Job config is ', job_config);
					/*
					 * For a config we should have 3 dimensions - the namespace (outer most)
					 * Then the name of the setting (middle)
					 * Then an object which contains the "type" and the value. (innermost)
					 */
					if (typeof job_config[target_namespace] !== 'undefined') {
						_.each(job_config[target_namespace], function (properties, name) {
							$scope.$parent.job_config[target_namespace + ":" + name]=properties.value
						});
					}
				});
			}
		}
	];
	return controller;
});
