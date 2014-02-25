define(['underscore'], function (_) {	
	"use strict";
	var controller=['$scope', '$modalInstance', '$log', 'tool',
	    /*
		 * This controller is used to manage the create job dialog - which is used to 
		 * choose a tool and data file so that a user can create a new job and get a
		 * job configuration form.
		 */
		
		function ($scope, $modalInstance, $log, tool) {
			$scope.jobdata={};
			$scope.jobdata['tool']=tool;
			
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
