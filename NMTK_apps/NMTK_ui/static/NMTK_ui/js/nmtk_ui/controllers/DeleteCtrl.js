define([], function () {	
	"use strict";
	var controller=['$scope','$modalInstance','api','id','name','type',
		function ($scope, $modalInstance, api, id, name, type) {
			$scope.api=api;
			$scope.id=id;
			$scope.name=name;
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
