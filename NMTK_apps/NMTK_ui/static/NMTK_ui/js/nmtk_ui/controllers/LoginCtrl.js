/*
 * Handle the case where we validate the login via the server, and display
 * the appropriate error message(s) when login fails.
 */
define([], function () {	
	"use strict";
	var controller=['$scope','$modalInstance', '$http','$timeout',
		function ($scope, $modalInstance, $http, $timeout) {
			$scope.logindata={'username': '',
							  'password': ''};
			$scope.failed_login=false;
			$scope.close=function () {
				$modalInstance.dismiss();
			};
			$scope.$on('login', function (evt, args) {
				$timeout(function () { $modalInstance.close()}, 0);
			});
			$scope.login=function () {
				$http({method: 'POST',
					   url: $scope.login_url,
					   data: $scope.logindata,
					   headers: {'X-CSRFToken': $scope.csrftoken }
				}).then(function (data) {
					$modalInstance.close();
				}, function (error) {
					$scope.failed_login=true;
				});
			}
		}
	];
	return controller;
});
