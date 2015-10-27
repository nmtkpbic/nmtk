/**
 * @license Nonmotorized Toolkit
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
define(['underscore'
        , 'text!fileInfoTemplate'
        , 'text!fileActionsCellTemplate'
        , 'text!viewJobModalTemplate'], 
		function (_, fileInfoTemplate, fileActionsCellTemplate,
				  viewJobModalTemplate) {	
	"use strict";
	var controller=['$scope','$timeout','$route','$modal','$location', '$log',
	                '$q', 'Restangular',
        function ($scope, $timeout, $route, $modal, $location, $log, $q,
        		  Restangular) {
			$scope.loginCheck();
			$scope.enableRefresh(['datafile']);
			$scope.changeTab('files');
			
			$scope.initialload=false;
			$scope.fileupload='';
			$scope.upload_uri=CONFIG.api_path + 'datafile/';
			$('#fileUpload').fileupload();
			$('#fileUpload').fileupload('option', {
				   url: CONFIG.api_path + 'datafile/',
				   paramName: 'file',
				   progressall: function (e, data) {
					    $('#progress .bar').show();
				        var progress = parseInt(data.loaded / data.total * 100, 10);
				        $('#progress .bar').css(
				            'width',
				            progress + '%'
				         );
				   },
				   done: function () { 
					   $scope.refreshData('datafile'); 
					   $timeout(function () {
						   $('#progress .bar').hide();
					   	   $('#progress .bar').css('width', '0%');
					   }, 1000);
				   }	 
			});
			
			$scope.openJobViewDialog=function(datafile) {
				$q.all([Restangular.all('job_results').getList({'datafile': datafile.id,
														        'limit': 1}),
						$scope.rest['job']]).then(function (results) {
					var job_uri=results[0][0].job;
					var job=_.find(results[1], function (this_job) {
						return (this_job.resource_uri == job_uri)
					});			
					$scope.view_job_opts = {
						backdrop: true,
						keyboard: true,
						backdropClick: true,
						scope: $scope,
						template:  viewJobModalTemplate,
						controller: 'ViewJobCtrl',
						resolve: { jobdata: function () { return job; } }
					};
					var d=$modal.open($scope.view_job_opts);
					d.result.then(function(result) {
						if (result) {
							result.put().then(function () {
								$scope.refreshData('job');
							});
						}
					});

				});
			};
			
			
			$scope.isComplete=function (record) {
				return /complete/i.test(record.status);
			}
			$scope.fileInfo=function (record) {
				$scope.opts = {
					    template:  fileInfoTemplate, // OR: templateUrl: 'path/to/view.html',
					    controller: 'FileInfoUpdateCtrl',
					    resolve:{'record': function () { return record; }},
					    scope: $scope
					  };
				
				var modal_dialog=$modal.open($scope.opts);
				
				modal_dialog.result.then(function(result) {
					$log.info('Result from dialog was ', result);
					$scope.refreshData('datafile');
				});
			}

			$scope.gridOptions= {
					 data: 'datafile_cache',
					 showFooter: false,
					 showFilter: true,
					 enableColumnResize: true,
					 enableRowSelection: false,
					 multiSelect: false,
					 plugins: [new ngGridFlexibleHeightPlugin()],
					 selectedItems: $scope.selections,
					 columnDefs: [  { width: '7%',
						              sortable: false,
						              cellClass: 'cellCenterOverflow',
						              cellTemplate: fileActionsCellTemplate,
						              displayName: ''}
						          , { field: 'name',
						              width: '30%',
						              displayName: 'File Name'}
						          , { field: 'status',
						              width: '20%',
						              displayName: 'Status'}
						          , { field: 'description',
						              width: '43%',
						              cellClass: 'cellWrapText',
						              displayName: 'Description'}
						          ],
					 showColumnMenu: false };
		}
	];
	return controller;
});
