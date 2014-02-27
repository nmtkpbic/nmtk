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
