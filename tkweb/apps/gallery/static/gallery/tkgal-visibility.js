$(document).keypress(function(ev) {
	if (/^[1-9]$/.exec(ev.key)) {
		var optionIndex = parseInt(ev.key);
		var radios = $('#tkgal-container > *:not(.hidden) input[type=radio]');
		var target = radios.eq(optionIndex - 1).val();
		radios.val([target]);
	}
});
