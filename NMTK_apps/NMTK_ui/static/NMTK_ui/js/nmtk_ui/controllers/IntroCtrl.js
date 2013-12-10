define([], function () {	
	"use strict";
	var controller=['$scope',
        function ($scope) {
			var linkCellTemplate = '<div class="ngCellText" ng-class="col.colIndex()">' +
								   '  <a href="#/tool-explorer/{{row.getProperty(col.field)}}">Explore</a>' +
								   '</div>';
			
			$scope.changeTab('introduction');
			$scope.gridOptions= {
					 data: 'rest.tool',
					 showFooter: false,
					 showFilter: true,
					 enableCellSelection: false,
					 enableColumnResize: false,
					 multiSelect: false,
					 selectedItems: $scope.selections,
					 columnDefs: [{field: 'name',
						           width: '85%',
						           displayName: 'Tool Name'},
						          {field: 'id',
						           width: '15%',
						           displayName: 'Explore',
						           enableCellEdit: false,
						           cellTemplate: linkCellTemplate
						          }],
					 showColumnMenu: false };
		}
	];
	return controller;
});
