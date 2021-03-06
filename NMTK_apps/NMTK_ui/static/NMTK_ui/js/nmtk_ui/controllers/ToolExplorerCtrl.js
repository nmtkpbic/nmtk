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
	var controller=['$scope','$routeParams','$log','$location','$modal', 
	                '$route','Restangular','$http','$q','$timeout',
        function ($scope, $routeParams, $log, $location, $modal, $route,
        		  Restangular, $http, $q, $timeout) {
			$scope.changeTab('toolexplorer');
			$scope.enableRefresh(['datafile','tool']);
			$scope.selections = [];
			$scope.gridOptions= {
					 data: 'tool_cache',
					 showFooter: false,
					 showFilter: true,
					 enableColumnResize: false,
					 multiSelect: false,
					 selectedItems: $scope.selections,
					 columnDefs: [{field: 'name',
						           displayName: 'Tool Name'}],
					 showColumnMenu: false };
			$scope.$watch('selections', function () {
				if ($scope.selections.length) {
					if ($routeParams.toolid != $scope.selections[0]['id']) {
						var path='/tool-explorer/'+$scope.selections[0]['id'];
						$location.path(path);
					}
					/*
					 * This is because the main django template uses this to
					 * set the URL for the tool explorer tab (so a user can
					 * click back over to this particular tab and get the same
					 * tool highlighted.)  It gives the impression that the 
					 * view is "static" (when it is really re-rendered when
					 * they visit the page.)
					 */
					$scope.$parent.current_tool=$scope.selections[0];
					$scope.sample_data_pending=false;
					$scope.sample_job_exists=false;
					$scope.sample_data_loaded=true;
					updateToolInfo($scope.selections[0]);
				}
			}, true);
					
			var updateToolInfo=function (tool) {
				$scope.sample_data_pending=false;
				$scope.sample_job_exists=false;
				$scope.sample_data_loaded=true;
				if ((typeof tool.config.sample !== 'undefined') &&
				    (typeof tool.config.sample.config !== 'undefined')) {
					$scope.sample_job_exists=true;
					if (typeof tool.config.sample.files !== 'undefined') {
						var file_checksums={};
						$scope.rest['datafile'].then(function (files) {
							_.each(files, function (f) {
								file_checksums[f.checksum]=/complete/i.test(f.status);
							});
							_.each(tool.config.sample.files, function (fdata) {
								if (typeof file_checksums[fdata.checksum] !== 'undefined') {
									/*
									 * The file is either loaded, or it is
									 * pending if the checksum exists in the 
									 * users file library.  If any of the 
									 * files are not complete, then 
									 * sample_data_pending is true.
									 */
									$scope.sample_data_pending=! file_checksums[fdata.checksum];
								} else {
									$scope.sample_data_loaded=false;
								}
							});
							if ($scope.sample_data_pending) {
								/*
								 * If it's pending, we will refresh periodically so
								 * we can determine if the data has completed loading.
								 */
								$timeout(function () { updateToolInfo(tool); }, 5000);
							}
						})
						
					}
				}
			}
			
			
			$scope.loadSampleData=function (tool) {
				/*
				 * Load the sample data, since there might be multiple files,
				 * we don't want to do the refresh until we've loaded up all
				 * the sample data - otherwise the UI will still show that 
				 * sample data needs to be loaded.  So we use a deferred here
				 * to ensure that things happen in the correct order.
				 */
				if (! $scope.user.is_active) {
					$scope.login({'post_func': function () { $scope.loadSampleData(tool) }
							     }
					);
				}
				$scope.rest['datafile'].then(function (files) {
					_.each(tool.config.sample.files, function (fdata) {
						var f=_.find(files, function (user_file) {
							if (user_file.checksum == fdata.checksum) {
								return true;
							}
						});
						if (typeof f === 'undefined') {
							Restangular.all('tool_sample_file').getList({'checksum': fdata.checksum,
							                                  		     'tool': tool.id}).then(function (sample_files) {
							    var deferred_things=[]
                  		    	_.each(sample_files, function (data) {
                  		    		deferred_things.push($http.get(data.load_sample_data));
							    });
							    $q.all(deferred_things).then(function (d) {
							    	$scope.refreshData('datafile').then(function (f) {
										updateToolInfo(tool);
									});
							    });
                  		    });
						}
					});
					
				});
			};
			
			$scope.$on('login', function (evt, args) {
				$route.reload();
			});
			
			if ($routeParams.toolid) {
//				$log.info('Toolid is ', $routeParams.toolid)
				$scope.$on('ngGridEventRows', function () {
//					$log.info('Got event!');
					$scope.rest.tool.then(function (tool_data) {
						angular.forEach(tool_data, function(data, index){
					         if (data.id == $routeParams.toolid){
//					        	 $log.info('Selecting', data, index);
					             $scope.gridOptions.selectItem(index, true);
					         }
						});
					});
				});
			}	
		}
	];
	return controller;
});
