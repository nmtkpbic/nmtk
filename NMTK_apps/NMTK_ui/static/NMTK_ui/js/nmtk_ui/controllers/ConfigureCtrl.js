define(['underscore'], function (_) {	
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
			var config_present=false;
			if (typeof $scope.$parent.job_config !== 'undefined') {
				config_present=true;
			} else {
				$scope.$parent.job_config={};
			}
			$log.info(config_present);
			$scope.sections={'properties': true,
							 'constants': false}
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
		//	});
		//	$scope.resources['job'].one(jobid).get().then(function (job_data) {
				$scope.job_data=job_data;
				var tool_id=job_data.tool.split('/').reverse()[1];
				var file_id=job_data.data_file.split('/').reverse()[1];
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
		//		});
		//		$scope.resources['tool'].one(tool_id).get().then(function (tool_data) {
					$scope.tool_name=tool_data.name;
					$scope.tool_data=tool_data;
					$scope.rest.datafile.then(function (files) {
						var file_data=undefined;
						_.each(files, function (data) {
							if (data.id == file_id) {
								file_data=data;
							}
						});
		//		});
		//			$scope.resources['datafile'].one(file_id).get().then(function (file_data) {
						// Compute a list of fields to select from for property selection
						// dialogs
						$scope.file_name=file_data.name;
						var fields=[]
						_.each(JSON.parse(file_data.fields), function (v) {
							fields.push({'label': v,
								         'value': v});
						});
						_.each(tool_data.config.input, function (data) {
							_.each(data.elements, function (property_data, name) {
								var config= {'display_name': property_data.display_name || property_data.name,
							        		'field': property_data.name,
							        		'required': property_data.required,
							        		'description': property_data.description,
							        		'type': property_data.type,
							        		'value': property_data['default']};
								
								if (data.type == 'File') {
									config.value=fields;
									if (! config_present) {
									  $scope.$parent.job_config[config.field]=config.field;
									}
								} else if (! config_present) {
									$scope.$parent.job_config[config.field]=property_data['default'];
								}
								$scope.tool_config.push(config);
							});
						});
						
					});
				});
			});
		
			$scope.setConfigureJob(jobid);
			$scope.enableRefresh([]);
			$scope.changeTab('configurejob');
			$scope.closeConfig=function () {
				$scope.$parent.job_uri=null;
				$scope.$parent.job_config={};
				$location.path('/job');
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
							    templateUrl:  'error.html', // OR: templateUrl: 'path/to/view.html',
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
		
			
			$scope.cloneConfig=function () {
				var modal_dialog=$modal.open({
					backdrop: true,
					scope: $scope,
				    templateUrl:  'cloneconfig.html', // OR: templateUrl: 'path/to/view.html',
				    controller: 'CloneConfigCtrl'
				});
				modal_dialog.result.then(function (job_config) {
					$log.info('Selected to clone', job_config);
					var other_config=JSON.parse(job_config);
					$log.info('Job config is ', job_config);
					var file_config=undefined;
					_.some($scope.tool_data.config.input, function (data) {
						   if (data.type == 'File') {
							   file_config=data.elements;
							   return true;
						   }
						   return false;
					});
					_.each(file_config, function (setting) {
						$scope.$parent.job_config[setting.name]=other_config[setting.name] 
					});
				});
			}
		}
	];
	return controller;
});
