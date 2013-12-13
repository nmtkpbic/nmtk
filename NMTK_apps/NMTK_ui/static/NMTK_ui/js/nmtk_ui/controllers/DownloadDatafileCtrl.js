define([], function () {	
	"use strict";
	var controller=['$scope','$log','$modalInstance','datafile',
        function ($scope, $log, $modalInstance, datafile) {
		$log.debug(datafile);
			$scope.datafile_id=datafile.id;
			var api_path=CONFIG.api_path;
			if (/\//.test(CONFIG.api_path)) {
				  api_path=CONFIG.api_path.substring(0, CONFIG.api_path.length-1);
			}
			$scope.download_url=datafile.download_url;
			if (datafile.srid) {
				$scope.spatial=true;
			} else {
				$scope.spatial=false;
			}
			$scope.file_url=datafile.file;
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
