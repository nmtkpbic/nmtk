define([], function () {	
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
