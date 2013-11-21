define([], function () {	
	"use strict";
	var controller=['$scope','$modalInstance','$log', 'jobdata', 
        function ($scope, $modalInstance, $log, jobdata) {
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
					       {'display_name': 'File Name',
							'field': 'file_name',
							'type': 'input',
					        'description':'The data file provided for this job', 
					        'disabled': true },
					       {'display_name': 'Job Status',
							'field': 'status',
							'type': 'input',
					        'description':'The current status of this job', 
					        'disabled': true }];
			$scope.close=function () {
				$modalInstance.close(false);
			}
			$scope.save=function () {
				$modalInstance.close($scope.jobdata)
			}
		}
	];
	return controller;
});
