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
	                '$q', 'Restangular','$window',
        function ($scope, $timeout, $route, $modal, $location, $log, $q,
        		  Restangular, $window) {
			$scope.loginCheck(true);
			$scope.enableRefresh(['datafile']);
			$scope.changeTab('files');
			
			$scope.initialload=false;
			$scope.fileupload='';
			$scope.upload_uri=CONFIG.api_path + 'datafile/';
			
			
			$scope.upload_files=[];
			$scope.$on('$dropletReady', function () {
				// Allow uploads of any files/any extension.
				$scope.upload_files.allowedExtensions([/.+/]);
			});
			
			/*
			 * when a file is added we can do the upload immediately
			 */
			$scope.percent=0;
			$scope.progressBarStyle={width: '0%'}
			$scope.$on('$dropletFileAdded', function (v) {
//				$timeout(function () {
				$scope.uploading = true;
					// Only iterate over the non-deleted files, since they haven't been uploaded yet.
					_.each($scope.upload_files.getFiles($scope.upload_files.FILE_TYPES.VALID), function (data) {
						var formData = new $window.FormData();
						var deferred = $q.defer();
						formData.append('file', data.file)
						formData.append('content_type', data.mimeType);
						formData.append('name', data.file.name);
						var httpRequest = new $window.XMLHttpRequest();
						httpRequest.open('post',
								         $scope.upload_uri + '?format=json',
								         true);
						httpRequest.setRequestHeader('X-CSRFToken',
								$scope.csrftoken);
						httpRequest.upload.onprogress = function (event) {
							var requestLength = data.file.size;
							$scope.$apply(function (scope) {
								if (event.lengthComputable) {
									scope.percent = Math.min(100, Math.round(100*(event.loaded/requestLength)))
									$log.info('Percent uploaded is', scope.percent, '%');
									$scope.progressBarStyle.width = scope.percent + '%';
									if (scope.percent == 100) {
										$timeout(function () {
											$log.debug('Disabling display...')
											scope.progressBarStyle.width = '0%';
											scope.percent=0;
											$scope.refreshData('datafile');
										}, 1000)
									}
								}
							});
						}
						httpRequest.send(formData);
						/* Mark it as deleted, since it's been uploaded now. */
						data.deleteFile();
					});
//				});
			});
			
//			
//			
//			$('#fileUpload').fileupload('option', {
//				   url: CONFIG.api_path + 'datafile/',
//				   paramName: 'file',
//				   progressall: function (e, data) {
//					    $('#progress .bar').show();
//				        var progress = parseInt(data.loaded / data.total * 100, 10);
//				        $('#progress .bar').css(
//				            'width',
//				            progress + '%'
//				         );
//				   },
//				   done: function () { 
//					   $scope.refreshData('datafile'); 
//					   $timeout(function () {
//						   $('#progress .bar').hide();
//					   	   $('#progress .bar').css('width', '0%');
//					   }, 1000);
//				   }	 
//			});
			
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
