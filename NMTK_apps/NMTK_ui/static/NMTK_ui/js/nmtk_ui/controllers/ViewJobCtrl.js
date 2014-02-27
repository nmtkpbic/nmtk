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
