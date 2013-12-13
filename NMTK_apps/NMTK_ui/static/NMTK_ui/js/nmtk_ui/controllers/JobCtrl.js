define(['text!jobActionsCellTemplate'
        , 'text!viewJobModalTemplate'
        , 'text!switchJobModalTemplate'], function (jobActionsCellTemplate,
        		viewJobModalTemplate, switchJobModalTemplate) {	
	"use strict";
	var controller=['$scope','$routeParams','$modal','$position','$location','$log',
		/*
		 * This is the controller for Jobs - in particular viewing and controlling
		 * a job.  Here we'll work with dialogs to create new jobs and then 
		 * choose/set the parameters for them.
		 */
		
		function ($scope, $routeParams, $modal, $position, $location, $log) {
			$scope.loginCheck();
			$scope.$watch('user', function () {
				$scope.loginCheck();
			});
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
		}
	];
	return controller;
});
