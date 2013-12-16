define([], function () {	
	"use strict";
	var controller=['$scope','$modalInstance','api','id','name','type','operation',
		function ($scope, $modalInstance, api, id, name, type, operation) {
			$scope.api=api;
			$scope.id=id;
			$scope.name=name;
			$scope.operation=operation;
			$scope.type=type;
			$scope.delete=function () {
				$modalInstance.close([api, id]);
			}
			$scope.close=function () {
				$modalInstance.dismiss();
			}
		}
	];
	return controller;
});
