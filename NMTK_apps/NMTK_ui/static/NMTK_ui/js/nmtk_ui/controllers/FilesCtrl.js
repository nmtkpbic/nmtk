define(['underscore'], function (_) {	
	"use strict";
	var controller=['$scope','$timeout','$route','$modal','$log',
        function ($scope, $timeout, $route, $modal, $log) {
			$log.info('In FilesCtrl');
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
			
			$scope.openDialog=function (record) {
				$scope.opts = {
					    templateUrl:  'file_info.html', // OR: templateUrl: 'path/to/view.html',
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
					 data: 'rest.datafile',
					 showFooter: false,
					 showFilter: true,
					 enableColumnResize: true,
					 enableRowSelection: false,
					 multiSelect: false,
					 selectedItems: $scope.selections,
					 columnDefs: [{field: 'name',
						           displayName: 'File Name'},
						          {field: 'status',
						           displayName: 'Import Status'},
						          {field: 'description',
						           displayName: 'Description'},
						          {field: 'actions',
						           displayName: 'Actions'}],
					 showColumnMenu: false };
		}
	];
	return controller;
});
