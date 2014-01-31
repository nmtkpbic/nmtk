define(['underscore'], function (_) {	
	"use strict";
	var controller=['$scope', '$modalInstance', '$log', 'tool','data_file',
	    /*
		 * This controller is used to manage the create job dialog - which is used to 
		 * choose a tool and data file so that a user can create a new job and get a
		 * job configuration form.
		 */
		
		function ($scope, $modalInstance, $log, tool, data_file) {
			$scope.jobdata={};
			$scope.jobdata['tool']=tool;
			$scope.jobdata['data_file']=data_file;
		
			$scope.getFileStr=function (o) {
				if (o.description) {
					return o.name + ' (' + o.description + ')';
				} else {
					return o.name;
				}
			}
			$scope.rest.tool.then(function(tools) {
				$scope.is_file_required=function() {			
					var tool_info;
					if (typeof $scope.jobdata['tool'] !== 'undefined') {
						tool_info=_.find(tools, function (t) { 
								return $scope.jobdata['tool'] == t.resource_uri; 
							}
						);
					}
					if (typeof tool_info !== 'undefined') {
						$log.info(tool_info);
						var file_config=_.find(tool_info.config.input, function (input) {
							$log.info('INPUT', input, input.type);
							if (input.type == 'File') {
								if (_.has(input, 'primary')) {
									// If primary exists, use that value.
									return input.primary;
								}
								// If primary isn't there, then just assume the first one
								// encountered is primary.
								return true;
							}
						});
						if (typeof file_config !== 'undefined') {
							$scope.file_label=file_config.label;
							$scope.file_description=file_config.description;
							return true;
						}
					}
					return false;
				}
			});
			$scope.close=function () {
				$modalInstance.dismiss();
			}
			$scope.save=function () {
				$modalInstance.close($scope.jobdata);
			}	
		}
	];
	return controller;
});
