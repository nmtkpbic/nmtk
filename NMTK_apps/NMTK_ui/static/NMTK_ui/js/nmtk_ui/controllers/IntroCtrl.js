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
define([], function () {	
	"use strict";
	var controller=['$scope','$location',
        function ($scope, $location) {
			var toolUrlCellTemplate = '<div class="ngCellText" title="{{row.getProperty(col.field)}}" ng-class="col.colIndex()">' +
								   '{{row.getProperty(col.field)}}' +
								   '</div>';

			var toolCellTemplate = '<div class="ngCellText" title="{{row.getProperty(col.field)}}" ng-class="col.colIndex()">' +
								   '  <a href="#/tool-explorer/{{row.entity.id}}">{{row.getProperty(col.field)}}</a>' +
								   '</div>';
			
			$scope.changeTab('introduction');
			$scope.selections=[];
//			$scope.$watch('selections', function () {
//				if ($scope.selections.length) {
//					$location.path('tool-explorer/' + $scope.selections[0].id);
//				}
//			}, true);
			$scope.gridOptions= {
					 data: 'tool_cache',
					 showFooter: false,
					 filterOptions: {filterText: '', useExternalFilter: false},
					 showFilter: true,
					 enableRowSelection: false,
					 enableColumnResize: false,
					 multiSelect: false,
					 selectedItems: $scope.selections,
					 plugins: [new ngGridFlexibleHeightPlugin()],
					 selectedItems: $scope.selections,
					 columnDefs: [  {field: 'tool_server',
						 			 cellTemplate: toolUrlCellTemplate,
						 			 displayName: 'Tool Server'},
						 			{field: 'name',
						             width: '75%',
						             cellTemplate: toolCellTemplate,
						             displayName: 'Tool Name'}
//						          , {field: 'id',
//						             width: '15%',
//						             displayName: 'Explore',
//						             enableCellEdit: false,
//						             cellTemplate: linkCellTemplate
//						            }
						           ],
					 showColumnMenu: false };
		}
	];
	return controller;
});
