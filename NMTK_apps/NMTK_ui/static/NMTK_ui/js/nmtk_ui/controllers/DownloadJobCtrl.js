define([], function () {	
	"use strict";
	var controller=['$scope','$log','$modalInstance','job',
        function DownloadJobCtrl($scope, $log, $modalInstance, job) {
			$scope.job_id=job.job_id;
			var api_path=CONFIG.api_path;
			$scope.format_types={'Comma Separated Values': 'csv',
								 'GeoJSON': 'geojson',
								 'Microsoft Excel Format (xls)': 'xls'};
			if (/\//.test(CONFIG.api_path)) {
				  api_path=CONFIG.api_path.substring(0, CONFIG.api_path.length-1);
			}
			$scope.download_url=job.results;
			$scope.close=function () {
				$modalInstance.dismiss();
			}
			$scope.getUrl=function(type) {
				return $scope.download_url + '?output=' + type;
			}
		}
	];
	return controller;
});
