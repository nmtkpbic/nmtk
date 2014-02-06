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
						} else {
							$scope.sections['input:'+i]=false
						}
						i+=1;
					});
					_.each(tool_data.config.output, function (data) {
						if (_.has(data,'expanded')) {
							$scope.sections['output:' + i]=data.expanded;
						} else {
							$scope.sections['output:'+i]=false
						}
						i+=1;
					});
					// If we don't have a config, we'll build a default using
					// the tool information
					var new_config=false;
					$scope.validation={};
					if (! $scope.$parent.job_config) {
						$scope.$parent.job_config={};
						$scope.$parent.job_config_files={};
						new_config=true;
					}
					_.each(['input','output'], function (section) {
						_.each(tool_data.config[section], function (data) {
							if (new_config) {
								$scope.$parent.job_config[data.namespace]={};
								$scope.$parent.job_config_files[data.namespace]='';
							}
							$scope.validation[data.namespace]={};
							_.each(data.elements, function (config_set) {
								if (new_config) {
									$scope.$parent.job_config[data.namespace][config_set.name]={};
									$scope.$parent.job_config[data.namespace][config_set.name]['type']=config_set.type;
									if (typeof config_set.default !== 'undefined' && data.type != 'File') {
										$scope.$parent.job_config[data.namespace][config_set.name]['value']=config_set.default;
									} else if (data.type == 'File') {
										$scope.$parent.job_config[data.namespace][config_set.name]['value']=config_set.name;
										$scope.$parent.job_config[data.namespace][config_set.name]['type']='property';
									}
								}
								$scope.validation[data.namespace][config_set.name]={ 'validation': config_set.validation,
																					 'type': config_set.type,
																					 'name': config_set.name,
																					 'default': config_set.default,
										        									 'choices': config_set.choices };
							});
						});
					});
					
					$scope.get_options=function (options) {
						var dataset=[];
						if (_.isArray(options)) {
							_.each(options, function (opt) {
								dataset.push({'label': opt, 'value': opt});
							});
							
						} else {
							_.each(options, function (value, key) {
								dataset.push({'label': key, 'value': value});
							});
						}
						return dataset;
					}
					
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
			$scope.rest.datafile.then(function (data_files) {
				$scope.updateFileFieldsFromResourceURI=function (key) {
					var resource_uri=$scope.$parent.job_config_files[key];
					if (typeof resource_uri !== 'undefined') {
						$log.info('Resource URI is ', resource_uri);
						
						var df=_.find(data_files, function (datafile) {
							return (datafile.resource_uri == resource_uri);
						});
						
						if (df) {
							var fields=[];
							_.each(JSON.parse(df.fields), function (v) {
								fields.push({'label': v,
									         'value': v});
							});
							$scope.file_fields[key]=fields;
						}
					} else {
						$scope.file_fields[key]=[];
					}
				}
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
			

			$scope.switchFieldMode=function (namespace, field) {
				var type=$scope.validation[namespace][field]['type'];
				var name=$scope.validation[namespace][field]['name'];
				var field_default=$scope.validation[namespace][field]['default'];
				if (type != 'property') {
					if ($scope.$parent.job_config[namespace][field]['type'] == 'property') {
						$scope.$parent.job_config[namespace][field]['type'] = type;
						$scope.$parent.job_config[namespace][field]['value']=field_default || '';
					} else {
						$scope.$parent.job_config[namespace][field]['type'] = 'property';
						$scope.$parent.job_config[namespace][field]['value']= name;
					}
				}
				return false;
			}
			
			
			
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
