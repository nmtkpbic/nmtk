/**
 * @license Non-Motorized Toolkit
 * Copyright (c) 2014 Open Technology Group Inc. (A North Carolina Corporation)
 * Developed under Federal Highway Administration (FHWA) Contracts:
 * DTFH61-12-P-00147 and DTFH61-14-P-00108
 * 
 * Redistribution and use in source and binary forms, with or without modification, 
 * are permitted provided that the following conditions are met:
 *     * Redistributions of source code must retain the above copyright notice, 
 *       this list of conditions and the following disclaimer.
 *     * Redistributions in binary form must reproduce the above copyright 
 *       notice, this list of conditions and the following disclaimer 
 *       in the documentation and/or other materials provided with the distribution.
 *     * Neither the name of the Open Technology Group, the name of the 
 *       Federal Highway Administration (FHWA), nor the names of any 
 *       other contributors may be used to endorse or promote products 
 *       derived from this software without specific prior written permission.
 *       
 *       THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
 *       "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT 
 *       LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS 
 *       FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL 
 *       Open Technology Group Inc BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
 *       SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT 
 *       LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF 
 *       USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED 
 *       AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
 *       OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT 
 *       OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF 
 *       SUCH DAMAGE.
 */
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
			$scope.enter_login = function(keyEvent) {
				  if (keyEvent.which === 13) {
					  $scope.login();
				  }
			}
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
