define([], function () {	
	"use strict";
	var controller=['$scope','$location','$modalInstance','$log',
        function ($scope, $location, $modalInstance, $log) {
			$log.info('In FeedbackCtrl');
			$log.info('Current location is ', $location.path());
			var values_list=['No Opinion', 'Works', 'Needs Help', 'No Way'];
			var values=[];
			_.each(values_list, function (v) {
				values.push({'label': v,
					         'value': v});
			});
			$scope.feedback=$scope.record;
			
			$scope.fields=[{'display_name': 'Transparency',
				        	'field': 'transparency',
					        'help':'Can you figure out what this page is supposed to do?',
					        'type': 'select',
					        'values': values},
						   {'display_name': 'Functionality',
					        'field': 'functionality',
						    'help':'Does this page do what it is supposed to?',
						    'type': 'select',
						    'values': values },
						   {'display_name': 'Usability',
					    	'field': 'usability',
					    	'help':'Does this page work well enough to be useful?',
					    	'type': 'select',
					        'values': values },
				 	       {'display_name': 'Performance',
					    	'field': 'performance',
					    	'help':'Does the page seem overly slow, or broken?',
					    	'type': 'select',
					        'values': values },
					       {'display_name': 'Comments',
					        'field': 'comments',
					        'help':'Enter your detailed comments here, especially if you ranked anything as \'Needs Help\' or \'No Way\'',
					        'type': 'textarea' }];
			
			$scope.save=function () {
				$modalInstance.close($scope.feedback);
			};
			
			$scope.close=function () {		
				$modalInstance.dismiss();
			};
		}
	];
	return controller;
});
