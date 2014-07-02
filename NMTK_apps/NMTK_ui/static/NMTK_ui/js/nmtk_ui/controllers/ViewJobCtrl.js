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
define([], function () {	
	"use strict";
	var controller=['$scope','$modalInstance','$log', 'jobdata', '$location',
        function ($scope, $modalInstance, $log, jobdata, $location) {
			$scope.jobdata=jobdata;
			$scope.fields=[{'display_name': 'Job Description',
							'field': 'description',
							'type': 'input',
					        'description':'Your description for this job', 
					        'disabled': false },
					       {'display_name': 'Tool Name',
							'field': 'tool_name',
							'type': 'input',
					        'description':'The tool used for this job', 
					        'disabled': true },
					       {'display_name': 'Job Status',
							'field': 'status',
							'type': 'input',
					        'description':'The current status of this job', 
					        'disabled': true },
					       {'display_name': 'Tool Status Time',
							'field': 'last_status',
							'type': 'input',
					        'description':'The last time we received a status update from the tool.', 
					        'disabled': true },
					       {'display_name': 'Tool Messages',
							'field': 'message',
							'type': 'textarea',
					        'description':'Any tool reported messages.', 
					        'disabled': true },];
			$scope.close=function () {
				$modalInstance.close(false);
			}
			$scope.save=function () {
				$modalInstance.close($scope.jobdata)
			}
			
			$scope.configureJob=function (jobdata) {
				$scope.$parent.configureJob(jobdata);
				$modalInstance.close(false);
			}
			$scope.downloadDatafile=function (jobdata) {
				$scope.$parent.downloadDatafile(null, jobdata);
				$modalInstance.close(false);
			}
			
			$scope.complete= /complete/i.test(jobdata.status);
			
			$scope.viewResults=function () {
				$log.info('New path will be ', '/view_results/' + jobdata.id);
				$location.path('/view_results/' + jobdata.id);
				$modalInstance.close(false);
			}
		}
	];
	return controller;
});
