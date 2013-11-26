define([], function () {	
	"use strict";
	var controller=['$scope','$modalInstance', 
		function ($scope, $modalInstance) {
			$scope.switchjob=function () { $modalInstance.close(); };
			$scope.close=function () { $modalInstance.dismiss(); };
		}
	];
	return controller;
});