define([], function () {	
	"use strict";
	var controller=['$scope','$routeParams','$log','$location','$modal', '$route',
        function ($scope, $routeParams, $log, $location, $modal, $route) {
			$scope.changeTab('toolexplorer');

			$log.info($scope.resources.tool);
			$scope.selections = [];
			$scope.gridOptions= {
					 data: 'rest.tool',
					 showFooter: false,
					 showFilter: true,
					 enableColumnResize: false,
					 multiSelect: false,
					 selectedItems: $scope.selections,
					 columnDefs: [{field: 'name',
						           displayName: 'Tool Name'}],
					 showColumnMenu: false };
			$scope.$watch('selections', function () {
				if ($scope.selections.length) {
					if ($routeParams.toolid != $scope.selections[0]['id']) {
						var path='#/tool-explorer/'+$scope.selections[0]['id'];
					}
					$scope.$parent.current_tool_id=$scope.selections[0]['id'];
				}
			}, true);
			if ($routeParams.toolid) {
//				$log.info('Toolid is ', $routeParams.toolid)
				$scope.$on('ngGridEventRows', function () {
//					$log.info('Got event!');
					$scope.rest.tool.then(function (tool_data) {
						angular.forEach(tool_data, function(data, index){
					         if (data.id == $routeParams.toolid){
//					        	 $log.info('Selecting', data, index);
					             $scope.gridOptions.selectItem(index, true);
					         }
						});
					});
				});
			}	
		}
	];
	return controller;
});
