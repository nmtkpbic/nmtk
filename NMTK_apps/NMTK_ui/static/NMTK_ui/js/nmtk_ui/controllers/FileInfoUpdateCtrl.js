define([], function () {	
	"use strict";
	var controller=['$scope', '$filter', '$log', '$modalInstance', 'record', 'Restangular',
        function ($scope, $filter, $log, $modalInstance, record, Restangular) {
			$scope.filedata=Restangular.copy(record); // Save the data we are editing in this scope.
			// Apply the filter to the data, since we need to display better in the template
			$scope.filedata.date_created=$filter('date')($scope.filedata.date_created, 'medium');
			// A list of lists, with the 5-set being field/attribute name
			// help-text, disabled true/false, and spatial true/false.
			
			$scope.filterSpatial= function(field) {
				if (field.hide_empty && !$scope.filedata[field.field]) {
					return false;
				} else if (field.spatial == true) {
					if ($scope.filedata.geom_type || ($scope.filedata.status == 'Import Failed')) {
						return true;
					} 
				}
				return true;
			}
			var srid_description=undefined;
			if ($scope.filedata.status == 'Import Failed') {
				srid_description='Specifying the proper SRID may allow this data to load.';
			} else {
				srid_description='The detected SRID for the uploaded file';
			}
			
			$scope.fields=[{'display_name': 'File Name',
				            'field': 'name',
				            'description':'The name of the uploaded file', 
				            'disabled': true, 
				            'spatial': false },
				           {'display_name': 'Status Message',
					        'field': 'status_message',
					        'description':'The reason the file failed to properly import', 
					        'disabled': true, 
					        'hide_empty': true,
					        'spatial': false },
				           {'display_name': 'Description',
					        'field': 'description',
					        'description':'A description/metadata for this file', 
					        'disabled': false, 
					        'spatial': false },
					       {'display_name': 'Date Uploaded',
				            'field': 'date_created',
				            'description':'The date/time when the file was uploaded', 
				            'disabled': true, 
				            'hide_empty': true,
				            'spatial': false }, 
					       {'display_name': 'Feature Count',
				            'field': 'feature_count',
				            'description':'The number of features (rows) of data in this file', 
				            'disabled': true, 
				            'hide_empty': true,
				            'spatial': false },
				           {'display_name': 'Geometry Type',
					        'field': 'geom_type',
					        'description':'The type of geometry for this data', 
					        'disabled': true, 
					        'hide_empty': true,
					        'spatial': true },
					       {'display_name': 'Spatial Reference Identifier (SRID)',
				            'field': 'srid',
				            'description':srid_description, 
				            'disabled': ($scope.filedata.status != 'Import Failed'), 
				            'hide_empty': false,
				            'spatial': true }	           
				            ]
			
		
			$scope.save=function () {
				$log.info('Data to save is', $scope.filedata);
				$scope.filedata.put().then(function (data) {
					$modalInstance.close(true);
				});
			}
			$scope.close=function() {
				$modalInstance.dismiss();
			}
		}
	];
	return controller;
});
