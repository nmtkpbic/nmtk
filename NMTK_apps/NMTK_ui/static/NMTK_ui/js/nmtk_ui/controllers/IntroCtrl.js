define([], function () {	
	"use strict";
	var controller=['$scope',
        function IntroCtrl($scope) {
			$scope.changeTab('introduction');
		}
	];
	return controller;
});
