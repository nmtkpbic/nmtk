define(['underscore', 'text!fileInfoTemplate', 'text!fileActionsCellTemplate'], 
		function (_, fileInfoTemplate, fileActionsCellTemplate) {	
	"use strict";
	var controller=['$scope','$timeout','$route','$modal','$location', '$log',
        function ($scope, $timeout, $route, $modal, $location, $log) {
			$scope.loginCheck();
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
			
			$scope.isComplete=function (record) {
				return /complete/i.test(record.status);
			}
			$scope.fileInfo=function (record) {
				$scope.opts = {
					    template:  fileInfoTemplate, // OR: templateUrl: 'path/to/view.html',
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
					 plugins: [new ngGridFlexibleHeightPlugin()],
					 selectedItems: $scope.selections,
					 columnDefs: [{field: 'name',
						           width: '30%',
						           displayName: 'File Name'},
						          {field: 'status',
						           width: '20%',
						           displayName: 'Status'},
						          {field: 'description',
						           width: '45%',
						           cellClass: 'cellWrapText',
						           displayName: 'Description'},
						          {
						           width: '5%',
						           sortable: false,
						           cellClass: 'cellCenterOverflow',
						           cellTemplate: fileActionsCellTemplate,
						           displayName: ''},
						          ],
					 showColumnMenu: false };
		}
	];
	return controller;
});
