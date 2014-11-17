/**
 * @license Non-Motorized Toolkit
 * Copyright (c) 2014 Open Technology Group Inc. (A North Carolina Corporation)
 * Developed under Federal Highway Administration (FHWA) Contracts:
 * DTFH61-12-P-00147 and DTFH61-14-P-00108
 * 
 * Redistribution and use in source and binary forms, with or without modification, 
 * are permitted provided that the following conditions are met:
 *     * Redistributions of source code must retain the above copyright notice, 
 *       this list of conditions and the following disclaimer.
 *     * Redistributions in binary form must reproduce the above copyright 
 *       notice, this list of conditions and the following disclaimer 
 *       in the documentation and/or other materials provided with the distribution.
 *     * Neither the name of the Open Technology Group, the name of the 
 *       Federal Highway Administration (FHWA), nor the names of any 
 *       other contributors may be used to endorse or promote products 
 *       derived from this software without specific prior written permission.
 *       
 *       THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
 *       "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT 
 *       LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS 
 *       FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL 
 *       Open Technology Group Inc BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
 *       SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT 
 *       LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF 
 *       USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED 
 *       AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
 *       OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT 
 *       OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF 
 *       SUCH DAMAGE.
 */
define(['underscore'], function (_) {	
	"use strict";
	var controller=['$scope', '$log', '$timeout', 'Restangular',
	                '$modalInstance', 'ramp',
	               
        function ($scope, $log, $timeout, Restangular, $modalInstance, ramp) {
			/*
			 * So first we need to make sure that we have the list
			 * of available color ramps.
			 * 
			 * If an invalid ramp is selected, start out by setting the
			 * default ramp to the selected ramp.
			 */
			$scope.selected={'ramp_id': ramp['ramp_id'],
					         'reverse': ramp['reverse']};

			Restangular.all('color_style').getList().then(function (styles) {
				$scope.color_styles=styles;
				$scope.default_style=_.find(styles, function (style) {
					return style.default;
				});
				if (_.isUndefined($scope.default_style) && style.length) {
					$scope.default_style = style[0];
				}
				$scope.current_style=_.find(styles, function (style) {
					return style.id == ramp['ramp_id'];
				});
				if (_.isUndefined($scope.current_style)) {
					$scope.current_style=$scope.default_style;
				}
				if ($scope.selected_style.length == 0) {
					$scope.selected_style.push($scope.current_style);
				}
				/*
				 * Get a list of the available categories for the ramps, and
				 * then generate that as a list for the drop-down in the UI.
				 * 
				 * Default to choosing the category that corresponds to the
				 * currently selected ramp.
				 */
				$scope.categories=_.uniq(_.pluck(styles, 'category'))
				
				$scope.selected['category']=$scope.current_style.category;
				$scope.updateFilters();
			});
			
			
			$scope.updateFilters=function (category) {
				if (! _.isUndefined(category)) {
					$scope.selected['category'] = category;
				}
				$scope.filtered_color_styles.length=0
				_.each($scope.color_styles,function (v) {
					if (v.category == $scope.selected['category']) {
						$scope.filtered_color_styles.push(v);
					}
				});
			}
			
			$scope.toggleReverse=function () {
				if ($scope.selected.reverse != "true") {
					$scope.selected.reverse="true";
				} else {
					$scope.selected.reverse="false";
				}
			}
			
			$scope.filtered_color_styles=[];
			$scope.selected_style = [];
			$scope.gridOptions= {
				 data: 'filtered_color_styles',
				 selectedItems: $scope.selected_style,
				 showFooter: false,
				 showFilter: false,
				 headerRowHeight: 0,
				 enableColumnResize: false,
				 enableRowSelection: true,
				 multiSelect: false,
				 columnDefs: [  { field: 'ramp_graphic',
					              cellTemplate: '<div class="ngCellText" ng-class="col.colIndex()"><span ng-cell-text><img src="{{row.entity.ramp_graphic}}?reverse={{selected.reverse}}" /></span></div>',
//					              width: '',
					              displayName: 'Ramp Graphic'}
					          ],
				 showColumnMenu: false 
			};
			
			$scope.cancel=function () {
				$modalInstance.dismiss();
			}
			$scope.close=function () {
				if ($scope.selected_style.length) {
					$modalInstance.close({'ramp_id': $scope.selected_style[0].id,
						                  'reverse': $scope.selected.reverse });
				} else {
					$modalInstance.dismiss();
				}
			}
			

		}			
	];
	return controller;
});
