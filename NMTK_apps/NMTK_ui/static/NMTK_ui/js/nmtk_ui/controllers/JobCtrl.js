define([], function () {	
	"use strict";
	var controller=['$scope','$routeParams','$modal','$position','$location','$log',
		/*
		 * This is the controller for Jobs - in particular viewing and controlling
		 * a job.  Here we'll work with dialogs to create new jobs and then 
		 * choose/set the parameters for them.
		 */
		
		function ($scope, $routeParams, $modal, $position, $location, $log) {
			if (! $scope.user.is_active ) {
				$scope.login($location.path());
				$location.path('/');
			}
			$scope.enableRefresh(['job']);
			$scope.refreshData('job');
			//var jobid=$routeParams.jobid;
			$log.info('In JobCtrl');
			$scope.changeTab('viewjob');
			
			$scope.openDialog=function(job) {
				$log.info('Got (openDialog)', job);
				$scope.view_job_opts = {
					backdrop: true,
					keyboard: true,
					backdropClick: true,
					templateUrl:  'view_job.html', // OR: templateUrl: 'path/to/view.html',
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
		
			$scope.importResults=function (job) {
				$log.info('Got (importResults)', job);
			};
			
			$scope.viewResults=function (job) {
				$scope.$parent.results_job=job;
				$location.path('/results/' + job.id + '/');
			};
		}
	];
	return controller;
});
