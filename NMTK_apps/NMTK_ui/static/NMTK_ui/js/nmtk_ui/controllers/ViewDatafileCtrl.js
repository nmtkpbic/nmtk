define(['underscore','leaflet'], function (_, L) {
	"use strict";
	var controller=['$scope','$routeParams','$location','$log','$http',
	                '$timeout', 'leafletData','Restangular', '$q',
        /*
		 * A variant of the ViewResults Controller that uses leaflet-directive 
		 * rather than leaflet directly.
		 */
	        
		function ($scope, $routeParams, $location, $log, $http, $timeout, 
				  leafletData, Restangular, $q) {
			$scope.loginCheck();
			$scope.changeTab('datafile_view');
			$scope.$parent.results_uri=$location.path();
			if (/^\d+$/.test($routeParams.id)) {
				$scope.source_path='/files';
				$timeout(function () { getDatafile($routeParams.id); }, 0);
			} else {
				$scope.source_path='/job';
				$timeout(function () { getJobInfo($routeParams.id); }, 0);
			}
			
			$log.debug('Parameters are ', $routeParams);
			/*
			 * A function that, when given a job identifier, locates the 
			 * primary results for that job and then loads it's respective
			 * data file.
			 */
			var getJobInfo=function (job_id) {
				$scope.rest['job'].then(function (data) {
					$scope.refreshData('datafile');
					$scope.job_api=_.find(data, function (row) {
						if (row.id ==  job_id) {
							return true;
						}
					});
					if (typeof $scope.job_api === 'undefined') {
						// Do something here, because the job is not defined,
						// they probably used a bookmark for a deleted job
						// or are trying to see something they don't have
						// access to.
						$scope.$parent.preview_datafile_api=undefined;
						$scope.$parent.preview_job_api=undefined;
						$location.path($scope.source_path);
					}
					var results_file=_.find($scope.job_api.results_files, function (datafile) {
						return datafile.primary;
					});

					if (typeof results_file !== 'undefined') {
						getDatafile(results_file.datafile.split('/').reverse()[1]);
					} else {
						// they specified a job that has no complete 
						// primary results
						$scope.$parent.preview_datafile_api=undefined;
						$scope.$parent.preview_job_api=undefined;
						$location.path($scope.source_path);
					}
				});
			}
				
			var getDatafile=function (datafile_id) {
				$scope.rest['datafile'].then(function (data) {
					$scope.datafile_api=_.find(data, function(row) {
						// Only allow viewing of complete files, since
						// others are not visible for this page.
						if ((datafile_id == row.id) &&
							(/complete/i.test(row.status))) {
							return true;
						}
					});
					$log.info('Datafile API is ', $scope.datafile_api);
					if (typeof $scope.datafile_api === 'undefined') {
						$scope.$parent.preview_datafile_api=undefined;
						$scope.$parent.preview_job_api=undefined;
						$location.path($scope.source_path);
					} else {			
						
						process_data();
					}
				});
			}
			
						
			$scope.filterOptions= { filterText: "",
									userExternalFilter: true };
							
			$scope.totalServerItems=0;
			$scope.selections=[];
			$scope.page_size=100;
			$scope.pagingOptions= {
			};
			$scope.columnOptions=[];
			$scope.sortInfo= { fields: ['nmtk_id'],
							   directions: ['asc'] };

			/*
			 * Note: This relies on leaflet being available...
			 */
			function getBounds(bbox) {
				var southWest = new L.LatLng(bbox[2], bbox[0]);
				var northEast = new L.LatLng(bbox[3], bbox[1]);	
				return L.latLngBounds(southWest, northEast);
			}
			
			$scope.$on('ngGridEventScroll', function (e) {
				$log.info('Got paging event', e);
				$scope.getPagedDataAsync($scope.page_size, $scope.paging_offset+$scope.page_size,
						                 $scope.filterOptions.filterText,$scope.sort_field);
			});
		            				
			
			$scope.getPagedDataAsync=function(pageSize, offset, searchText, order){
				$scope.paging_offset=offset;
				if ($scope.datafile_api) {
					var options={offset: offset,
							     limit: pageSize,
							     search: searchText,
							     order_by: order,
							     format: 'pager'};
					$log.info('Making request for ', $scope.datafile_api.download_url, options);
					$http.get($scope.datafile_api.download_url, {params: options}).success(function (data) {
						$scope.totalServerItems=data.meta.total;
						$scope.pagingOptions.currentPage=(data.meta.offset/data.meta.limit)+1
						if ($scope.paging_offset > 0) {
							$log.info('Concatenating!')
							$scope.data= $scope.data.concat(data.data);
		//					$scope.data.push.apply($scope.data, data.data);
						} else {
							$scope.data=data.data;
						}
						if ($scope.columnOptions.length == 0) {
							$scope.columnOptions=[]
							var visible=false;
							var i=0;
							var result_field=$scope.datafile_api.result_field;
							if (result_field) {
								// If there is a result field, no need to
								// show others.
								i=99;
							}
							_.each(data.data[0], function (col_val, col_name) {
								if ((i <= 1) || (col_name=='nmtk_id') || 
								    (col_name == result_field)) {
									visible=true;
								} else {
									visible=false;
								}
								$scope.columnOptions.push({ field: col_name,
									                        visible: visible});
								i += 1;
							});
//							}
						}
					});
				}
			};
			$scope.olcount=0;
			
			// Whenever a feature is selected in the table, we will match that feature in
			// the view window...
			$scope.$watch('selected_features', function (newVal, oldVal) {
				var ids=[];
				_.each($scope.selected_features, function (data) {
					ids.push(data.nmtk_id);
				});
				if ($scope.spatial) {
					if ($scope.leaflet.layers.overlays['highlight' + $scope.olcount]) {
						delete $scope.leaflet.layers.overlays['highlight'+$scope.olcount];
					}
				}
				$scope.olcount += 1;
				if ($scope.spatial) {
					if (ids.length) {
						$scope.leaflet.layers.overlays['highlight'+$scope.olcount]= {
					            name: 'Selected Layers',
					            type: 'wms',
					            visible: true,
					            url: $scope.datafile_api.wms_url,
					            layerOptions: { layers: "highlight",
					            	            ids: ids.join(','),
					                    		format: 'image/png',
					                    		transparent: true }
					    }
					}
				}
				$log.info('Got items selected!');
				// If nothing is selected, select the first item
				if ($scope.selected_selected.length == 0) {
					$timeout(function () {
//						$scope.gridOptions2.selectItem(0, true);
					}, 100);
				}
			}, true);
			
			// When someone selects items via the "results" grid it goes
			// into selections, which we then need to copy over to selected_features
			
			$scope.$watch('selections', function (newVal, oldVal) {
				$log.info('Got selections!')
				// If we're working with results from a map-click, then clicking on
				// a row will remove those results.
				if ($scope.feature_query_results) {
					$scope.selected_features=[];
					$scope.selected_selected.length=0;
					$scope.feature_query_results=false;
				}
				var ids=[]
				_.each($scope.selected_features, function (data) {
					ids.push(data.nmtk_id);
				});
				if (! $scope.selected_features) {
					$scope.selected_features=newVal;
				} else {
					_.each(newVal, function (data) {
						if (! _.contains(ids, data.nmtk_id)) {
							$scope.selected_features.push(data);
						}
					})
				}
		//		$scope.selected_features=newVal;
			},true);
			
			// We watch reloadData to signal to ng-grid that it should reset its 
			// selections and reload data.  This is because Ng-grid does not have a
			// method by which we can *unselect* selected rows (easily.)
			$scope.reloadData=1;
			/*
			 * When the selection is cleared, just truncate all the lists of selected 
			 * stuff to 0 and then reload the data for the grid (to unselect items.)
			 */
			$scope.clearSelection=function() {
				_.each($scope.selected_features, function (v, index) {
					$scope.gridOptions2.selectItem(index, false);
				});
				_.each($scope.data, function (v, index) {
					$scope.gridOptions.selectItem(index, false);
				});
				$scope.selected_features=[];
			}
			
			
			$scope.$on('leafletDirectiveMap.click', function(ev, e) {
				leafletData.getMap().then(function (leafletMap) {
			        $scope.clearSelection();
			        $scope.feature_query_results=true
					var config={params: {lat: e.leafletEvent.latlng.lat,
										 lon: e.leafletEvent.latlng.lng,
										 zoom: leafletMap.getZoom(),
										 format: 'query'}};
					$http.get($scope.datafile_api.download_url, config).success(function (data) {
						//$log.info('Result from query was %s', data);
						$scope.selected_features=data.data;
					})
				});
		    });
			function ngGridLayoutPlugin () {
			    var self = this;
			    this.grid = null;
			    this.scope = null;
			    this.init = function(scope, grid, services) {
			        self.domUtilityService = services.DomUtilityService;
			        self.grid = grid;
			        self.scope = scope;
			    };
			
			    this.updateGridLayout = function () {
			        if (!self.scope.$$phase) {
			            self.scope.$apply(function(){
			                self.domUtilityService.RebuildGrid(self.scope, self.grid);
			            });
			        }
			        else {
			            // $digest or $apply already in progress
			            self.domUtilityService.RebuildGrid(self.scope, self.grid);
			        }
			    };
			}
			
			$scope.selected_selected=[];

		
		    $scope.gridOptions2={data: 'selected_features',
		    		             showColumnMenu: true,
		    		             multiSelect: false,
		    		             columnDefs: 'columnOptions',
		    		             showFooter: false,
		    		             selectedItems: $scope.selected_selected}
		    
			$scope.gridOptions= {data: 'data',
								 columnDefs: 'columnOptions',
		//						 enablePaging: true,
								 showFooter: true,
								 multiSelect: true,
								 selectedItems: $scope.selections,
								 totalServerItems: 'totalServerItems',
								 sortInfo: $scope.sortInfo,
		//						 pagingOptions: $scope.pagingOptions,
								 filterOptions: $scope.filterOptions,
								 useExternalSorting: true,
			                     showColumnMenu: true };
			_.each(['filterOptions', 'sortInfo'], function (item) {
				$scope.$watch(item, function (newVal, oldVal) {
					$log.info('Got change to ', item, newVal, oldVal);
					if (newVal !== oldVal) {
						if ($scope.sortInfo.fields.length) {
						   $scope.sort_field=$scope.sortInfo.fields[0]
						   if ($scope.sortInfo.directions[0] == 'desc') {
							   $scope.sort_field='-'+$scope.sort_field;
						   }
						}
						$scope.getPagedDataAsync($scope.page_size, 
								                 0,
								                 $scope.filterOptions.filterText,
								                 $scope.sort_field);
					}
				}, true);
			});
			
			/* 
			 * The leaflet directive code is somewhat broke in that if 
			 * bounds is specified, but set to a variable set to null, it is then 
			 * totally ignored (the watch isn't setup.)  To mitigate this, set the
			 * bounds to some reasonable value to start with, then we can change it
			 * later since the $watch is there...
			 */
			$scope.bounds={southWest: { lat: 44.81773,
				                        lng: -93.499378},
				           northEast: { lat: 45.076137,
				                        lng: -93.16212 }
						  };
				
			$scope.bounds=getBounds([-93.499378, -93.16212,
									 44.81773, 45.076137]);
			$scope.center=$scope.bounds.getCenter();
			$scope.center.zoom=4;
			
			var style=function (feature) {
				geojsonMarkerOptions = {
						    radius: 8,
						    fillColor: "#ff7800",
						    color: "#000",
						    weight: 1,
						    opacity: 1,
						    fillOpacity: 0.8
						};
				return geojsonMarkerOptions;
			}
			$scope.leaflet={'defaults': { maxZoom: 18
										},
					        'layers': {
					        		   'baselayers': { osm: { name: 'OpenStreetMap',
										                      type: 'xyz',
										                      url: 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
										                      layerOptions: {
										                         subdomains: ['a', 'b', 'c'],
										                         attribution: '© OpenStreetMap contributors',
										                         continuousWorld: true
										                      }
										                     }
										        	 },
									   'overlays': { }
					        }
					        
			}
			
			// Get the information about the input file - used to determine if this
			// job has a spatial component to it and get the various URLs for data
			// display.
			var process_data=function () {
				if ($scope.datafile_api.geom_type) {
					$scope.bounds=getBounds($scope.datafile_api.bbox);
					$scope.spatial=true;
				} else {
					$scope.spatial=false;
				}
				if ($scope.datafile_api.result_field) {
					$scope.$parent.data_file_tab_name="Results";
				} else {
					$scope.$parent.data_file_tab_name="Data";
				}
				$scope.getPagedDataAsync($scope.page_size, 0, '', 'nmtk_id');	
				if ($scope.spatial) {
					$scope.leaflet.layers.overlays['results']= {
				            name: 'Tool Results',
				            type: 'wms',
				            visible: true,
				            url: $scope.datafile_api.wms_url,
				            layerOptions: { layers: $scope.datafile_api.layer,
				                    		format: 'image/png',
				                    		transparent: true }
				    };
				}
			};
			
			
			
			
			
			// Handle the case when a user clicks on a spot on the map, we need to then
			// fire off a GetFeatureInfo requests against the WMS.
			
		     
			$scope.close=function () {
				$scope.$parent.results_uri=null;
				$location.path($scope.source_path);
			}
		}
	];
	return controller;
});

