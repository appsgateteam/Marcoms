12.0.0.2---> index updated

12.0.0.3---> 

1. Solved issues related to internal picking from the requisition and one new field added in requisition for delivery to it will get the picking type by default
2. Passed job order, user, analytic account, a project from requisition to internal picking.


12.0.0.4--->

1.solve the issue of the internal_picking_id on creation of purchase order and picking.

12.0.0.5
	Solve internal picking type issue, Add warning for internal picking.
12.0.0.6
    Solve state change issue, and make field readonly.

12.0.0.7
    state changes and rights added.

12.0.0.8
    change vendor field to required.

Date 17th march 2020
12.0.0.8
	- purchase order operation select , thats required field vendor other wise its not required.
	- vendor not given then internal transfer will generate.
	- receive date readonly.


Date 26th march 2020
version 12.0.0.9
issues and improvement:-
	--> vendors field should be required field for the purchase order not for the internal picking in “material requisition” 
	--> purchase requisition-->received date field should be non editable .
	--> purchase order operation select , thats required field vendor other wise its not required.
	--> vendor not given then internal transfer will generate.
	--> vendors field should be required field for the purchase order not for the internal picking in “material requisition” 
	--> purchase requisition-->received date field should be non editable .
	--> Add Check Box in the cost sheet --> picking details tab(if the it is checked than manually visible source and destination field will be visible)
	--> Source location is wrong passed(NOT IMPROVED)
	--> purchase requisition smart button hide,if not available.
	--> In Purchase Requisition "Construction project" field  should be fetched from cost sheet project name
	--> internal picking and ref not given , select manully all fields