define(['text!jobActionsCellTemplate'
        , 'text!viewJobModalTemplate'
        , 'text!switchJobModalTemplate'
        , 'text!jobDescriptionCellTemplate'
        , 'text!jobStatusCellTemplate'], function (jobActionsCellTemplate,
        		viewJobModalTemplate, switchJobModalTemplate,
        		jobDescriptionCellTemplate, jobStatusCellTemplate) {	
	"use strict";
	var controller=['$scope','$routeParams','$modal','$position','$location','$log',
		/*
		 * This is the controller for Jobs - in particular viewing and controlling
		 * a job.  Here we'll work with dialogs to create new jobs and then 
		 * choose/set the parameters for them.
		 */
		
		function ($scope, $routeParams, $modal, $position, $location, $log) {
			$scope.loginCheck();
			$scope.enableRefresh(['job']);
			$scope.refreshData('job');
			//var jobid=$routeParams.jobid;
			$log.info('In JobCtrl');
			$scope.changeTab('viewjob');
			
			$scope.openDialog=function(job) {
				$scope.view_job_opts = {
					backdrop: true,
					keyboard: true,
					backdropClick: true,
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
			};		
			$scope.gridOptions= {
					 data: 'rest.job',
					 showFooter: false,
					 showFilter: true,
					 rowHeight: 75,
					 enableColumnResize: false,
					 enableRowSelection: false,
					 multiSelect: false,
					 plugins: [new ngGridFlexibleHeightPlugin()],
					 selectedItems: $scope.selections,
					 columnDefs: [{width: '50%',
						 		   sortable: false,
						           cellTemplate: jobDescriptionCellTemplate,
						           displayName: 'Job Description'},
						          {field: 'status',
						           width: '15%',
						           displayName: 'Status'},
						          {width: '29%',
					        	   sortable: false,
						           cellTemplate: jobStatusCellTemplate,
						           displayName: 'Tool Reported Status'},
						          {width: '6%',
						           sortable: false,
						           cellClass: 'cellCenterOverflow',
						           cellTemplate: jobActionsCellTemplate,
						           displayName: ''},
						          ],
					 showColumnMenu: false };
		}
	];
	return controller;
});
