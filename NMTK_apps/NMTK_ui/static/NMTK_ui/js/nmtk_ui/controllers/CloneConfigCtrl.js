define([], function () {	
	"use strict";
	var controller=['$scope','$modalInstance',
	    function ($scope, $modalInstance) {
			$scope.selected={'item': undefined};
			$scope.clone=function () {
				$modalInstance.close($scope.selected.item);
			}
			$scope.close=function () {
				$modalInstance.dismiss();
			}
		}
	];
	return controller;
});
