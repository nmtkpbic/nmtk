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
	var controller=['$scope','$location','$modalInstance','$log',
        function ($scope, $location, $modalInstance, $log) {
			var values_list=['No Opinion', 'Works', 'Needs Help', 'No Way'];
			var values=[];
			_.each(values_list, function (v) {
				values.push({'label': v,
					         'value': v});
			});
			$scope.feedback=$scope.record;
			
			$scope.fields=[{'display_name': 'Transparency',
				        	'field': 'transparency',
					        'help':'Can you figure out what this page is supposed to do?',
					        'type': 'select',
					        'values': values},
						   {'display_name': 'Functionality',
					        'field': 'functionality',
						    'help':'Does this page do what it is supposed to?',
						    'type': 'select',
						    'values': values },
						   {'display_name': 'Usability',
					    	'field': 'usability',
					    	'help':'Does this page work well enough to be useful?',
					    	'type': 'select',
					        'values': values },
				 	       {'display_name': 'Performance',
					    	'field': 'performance',
					    	'help':'Does the page seem overly slow, or broken?',
					    	'type': 'select',
					        'values': values },
					       {'display_name': 'Comments',
					        'field': 'comments',
					        'help':'Enter your detailed comments here, especially if you ranked anything as \'Needs Help\' or \'No Way\'',
					        'type': 'textarea' }];
			
			$scope.save=function () {
				$modalInstance.close($scope.feedback);
			};
			
			$scope.close=function () {		
				$modalInstance.dismiss();
			};
		}
	];
	return controller;
});
