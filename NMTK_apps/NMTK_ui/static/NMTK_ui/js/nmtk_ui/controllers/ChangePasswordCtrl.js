define([], function () {	
	"use strict";
	var controller=['$scope','$modalInstance',
		function ChangePasswordCtrl($scope, $modalInstance) {
			$scope.password={'password': '',
					         'password_repeat': '',
					         'old_password': ''};
			$scope.close=function () {
				$modalInstance.dismiss();
			};
			$scope.matchPassword=function () {
				if ($scope.password.password && $scope.password.password_repeat) {
					if (($scope.password.password == $scope.password.password_repeat) &&
						 $scope.password.old_password.length && $scope.password.password.length){
						return true;
					}
				}
				return false;
			}
			$scope.save=function () {
				// Change the password here.
				$modalInstance.close($scope.password);
			};
		}
	];
	return controller;
});
