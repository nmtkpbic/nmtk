define(['underscore'], function (_) {	
	"use strict";
	var controller=['$scope','$log','$modalInstance','api','id','name','type','operation',
	                'files', 'jobdata',
		function ($scope, $log, $modalInstance, api, id, name, type, operation, files,
				  jobdata) {
			$scope.api=api;
			$scope.id=id;
			$scope.name=name;
			$scope.operation=operation;
			$scope.type=type;
			$scope.jobs_in=[];
			$scope.jobs_out=[];
			
			if (files) {
				_.each(files[0], function (data) {
					var job=_.find(jobdata, function (j) {
						return (j.resource_uri == data.job);
					});
					$scope.jobs_in.push(job);
				});
				_.each(files[1], function (data) {
					var job=_.find(jobdata, function (j) {
						return (j.resource_uri == data.job);
					});
					$scope.jobs_out.push(job);
				});
			}
			
			$scope.delete=function () {
				$modalInstance.close([api, id]);
			}
			$scope.close=function () {
				$modalInstance.dismiss();
			}
		}
	];
	return controller;
});
