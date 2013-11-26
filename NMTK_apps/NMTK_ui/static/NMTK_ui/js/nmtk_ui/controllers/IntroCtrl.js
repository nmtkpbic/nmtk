define([], function () {	
	"use strict";
	var controller=['$scope',
        function ($scope) {
			$scope.changeTab('introduction');
		}
	];
	return controller;
});
