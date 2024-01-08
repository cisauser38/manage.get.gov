/**
 * @file get-gov.js includes custom code for the .gov registrar.
 *
 * Constants and helper functions are at the top.
 * Event handlers are in the middle.
 * Initialization (run-on-load) stuff goes at the bottom.
 */


var DEFAULT_ERROR = "Please check this field for errors.";

var INFORMATIVE = "info";
var WARNING = "warning";
var ERROR = "error";
var SUCCESS = "success";

// <<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>>
// Helper functions.

/** Makes an element invisible. */
function makeHidden(el) {
  el.style.position = "absolute";
  el.style.left = "-100vw";
  // The choice of `visiblity: hidden`
  // over `display: none` is due to
  // UX: the former will allow CSS
  // transitions when the elements appear.
  el.style.visibility = "hidden";
}

/** Makes visible a perviously hidden element. */
function makeVisible(el) {
  el.style.position = "relative";
  el.style.left = "unset";
  el.style.visibility = "visible";
}

/** Creates and returns a live region element. */
function createLiveRegion(id) {
  const liveRegion = document.createElement("div");
  liveRegion.setAttribute("role", "region");
  liveRegion.setAttribute("aria-live", "polite");
  liveRegion.setAttribute("id", id + "-live-region");
  liveRegion.classList.add("usa-sr-only");
  document.body.appendChild(liveRegion);
  return liveRegion;
}

/** Announces changes to assistive technology users. */
function announce(id, text) {
  let liveRegion = document.getElementById(id + "-live-region");
  if (!liveRegion) liveRegion = createLiveRegion(id);
  liveRegion.innerHTML = text;
}

/**
 * Slow down event handlers by limiting how frequently they fire.
 *
 * A wait period must occur with no activity (activity means "this
 * debounce function being called") before the handler is invoked.
 *
 * @param {Function} handler - any JS function
 * @param {number} cooldown - the wait period, in milliseconds
 */
function debounce(handler, cooldown=600) {
  let timeout;
  return function(...args) {
    const context = this;
    clearTimeout(timeout);
    timeout = setTimeout(() => handler.apply(context, args), cooldown);
  }
}

/** Asyncronously fetches JSON. No error handling. */
function fetchJSON(endpoint, callback, url="/api/v1/") {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', url + endpoint);
    xhr.send();
    xhr.onload = function() {
      if (xhr.status != 200) return;
      callback(JSON.parse(xhr.response));
    };
    // nothing, don't care
    // xhr.onerror = function() { };
}

/** Modifies CSS and HTML when an input is valid/invalid. */
function toggleInputValidity(el, valid, msg=DEFAULT_ERROR) {
  if (valid) {
    el.setCustomValidity("");
    el.removeAttribute("aria-invalid");
    el.classList.remove('usa-input--error');
  } else {
    el.classList.remove('usa-input--success');
    el.setAttribute("aria-invalid", "true");
    el.setCustomValidity(msg);
    el.classList.add('usa-input--error');
  }
}

/** Display (or hide) a message beneath an element. */
function inlineToast(el, id, style, msg) {
  if (!el.id && !id) {
    console.error("Elements must have an `id` to show an inline toast.");
    return;
  }
  let toast = document.getElementById((el.id || id) + "--toast");
  if (style) {
    if (!toast) {
      // create and insert the message div
      toast = document.createElement("div");
      const toastBody = document.createElement("div");
      const p = document.createElement("p");
      toast.setAttribute("id", (el.id || id) + "--toast");
      toast.className = `usa-alert usa-alert--${style} usa-alert--slim`;
      toastBody.classList.add("usa-alert__body");
      p.classList.add("usa-alert__text");
      p.innerHTML = msg;
      toastBody.appendChild(p);
      toast.appendChild(toastBody);
      el.parentNode.insertBefore(toast, el.nextSibling);
    } else {
      // update and show the existing message div
      toast.className = `usa-alert usa-alert--${style} usa-alert--slim`;
      toast.querySelector("div p").innerHTML = msg;
      makeVisible(toast);
    }
  } else {
    if (toast) makeHidden(toast);
  }
}

function _checkDomainAvailability(el) {
  const callback = (response) => {
    toggleInputValidity(el, (response && response.available), msg=response.message);
    announce(el.id, response.message);
    if (el.validity.valid) {
      el.classList.add('usa-input--success');
      // use of `parentElement` due to .gov inputs being wrapped in www/.gov decoration
      inlineToast(el.parentElement, el.id, SUCCESS, response.message);
    } else {
      inlineToast(el.parentElement, el.id, ERROR, response.message);
    }
  }
  fetchJSON(`available/?domain=${el.value}`, callback);
}

/** Call the API to see if the domain is good. */
const checkDomainAvailability = debounce(_checkDomainAvailability);

/** Hides the toast message and clears the aira live region. */
function clearDomainAvailability(el) {
  el.classList.remove('usa-input--success');
  announce(el.id, "");
  // use of `parentElement` due to .gov inputs being wrapped in www/.gov decoration
  inlineToast(el.parentElement, el.id);
}

/** Runs all the validators associated with this element. */
function runValidators(el) {
  const attribute = el.getAttribute("validate") || "";
  if (!attribute.length) return;
  const validators = attribute.split(" ");
  let isInvalid = false;
  for (const validator of validators) {
    switch (validator) {
      case "domain":
        checkDomainAvailability(el);
        break;
    }
  }
  toggleInputValidity(el, !isInvalid);
}

/** Clears all the validators associated with this element. */
function clearValidators(el) {
  const attribute = el.getAttribute("validate") || "";
  if (!attribute.length) return;
  const validators = attribute.split(" ");
  for (const validator of validators) {
    switch (validator) {
      case "domain":
        clearDomainAvailability(el);
        break;
    }
  }
  toggleInputValidity(el, true);
}

// <<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>>
// Event handlers.

/** On input change, handles running any associated validators. */
function handleInputValidation(e) {
  clearValidators(e.target);
  if (e.target.hasAttribute("auto-validate")) runValidators(e.target);
}

/** On button click, handles running any associated validators. */
function handleValidationClick(e) {
  const attribute = e.target.getAttribute("validate-for") || "";
  if (!attribute.length) return;
  const input = document.getElementById(attribute);
  runValidators(input);
}

// <<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>>
// Initialization code.

/**
 * An IIFE that will attach validators to inputs.
 *
 * It looks for elements with `validate="<type> <type>"` and adds change handlers.
 * 
 * These handlers know about two other attributes:
 *  - `validate-for="<id>"` creates a button which will run the validator(s) on <id>
 *  - `auto-validate` will run validator(s) when the user stops typing (otherwise,
 *     they will only run when a user clicks the button with `validate-for`)
 */
 (function validatorsInit() {
  "use strict";
  const needsValidation = document.querySelectorAll('[validate]');
  for(const input of needsValidation) {
    input.addEventListener('input', handleInputValidation);
  }
  const activatesValidation = document.querySelectorAll('[validate-for]');
  for(const button of activatesValidation) {
    button.addEventListener('click', handleValidationClick);
  }
})();

function removeForm(e, formLabel, isNameserversForm, addButton, formIdentifier){
  let totalForms = document.querySelector(`#id_${formIdentifier}-TOTAL_FORMS`);
  let formToRemove = e.target.closest(".repeatable-form");
  formToRemove.remove();
  let forms = document.querySelectorAll(".repeatable-form");
  totalForms.setAttribute('value', `${forms.length}`);

  let formNumberRegex = RegExp(`form-(\\d){1}-`, 'g');
  let formLabelRegex = RegExp(`${formLabel} (\\d+){1}`, 'g');
  // For the example on Nameservers
  let formExampleRegex = RegExp(`ns(\\d+){1}`, 'g');

  forms.forEach((form, index) => {
    // Iterate over child nodes of the current element
    Array.from(form.querySelectorAll('label, input, select')).forEach((node) => {
      // Iterate through the attributes of the current node
      Array.from(node.attributes).forEach((attr) => {
        // Check if the attribute value matches the regex
        if (formNumberRegex.test(attr.value)) {
          // Replace the attribute value with the updated value
          attr.value = attr.value.replace(formNumberRegex, `form-${index}-`);
        }
      });
    });

    // h2 and legend for DS form, label for nameservers  
    Array.from(form.querySelectorAll('h2, legend, label, p')).forEach((node) => {
      
      // If the node is a nameserver label, one of the first 2 which was previously 3 and up (not required)
      // inject the USWDS required markup and make sure the INPUT is required
      if (isNameserversForm && index <= 1 && node.innerHTML.includes('server') && !node.innerHTML.includes('*')) {
        // Create a new element
        const newElement = document.createElement('abbr');
        newElement.textContent = '*';
        newElement.setAttribute("title", "required");
        newElement.classList.add("usa-hint", "usa-hint--required");

        // Append the new element to the label
        node.appendChild(newElement);
        // Find the next sibling that is an input element
        let nextInputElement = node.nextElementSibling;

        while (nextInputElement) {
          if (nextInputElement.tagName === 'INPUT') {
            // Found the next input element
            nextInputElement.setAttribute("required", "")
            break;
          }
          nextInputElement = nextInputElement.nextElementSibling;
        }
        nextInputElement.required = true;
      }

      let innerSpan = node.querySelector('span')
      if (innerSpan) {
        innerSpan.textContent = innerSpan.textContent.replace(formLabelRegex, `${formLabel} ${index + 1}`);
      } else {
        node.textContent = node.textContent.replace(formLabelRegex, `${formLabel} ${index + 1}`);
        node.textContent = node.textContent.replace(formExampleRegex, `ns${index + 1}`);
      }
    });

    // Display the add more button if we have less than 13 forms
    if (isNameserversForm && forms.length <= 13) {
      console.log('remove disabled');
      addButton.removeAttribute("disabled");
    }

    if (isNameserversForm && forms.length < 3) {
      // Hide the delete buttons on the remaining nameservers
      Array.from(form.querySelectorAll('.delete-record')).forEach((deleteButton) => {
        deleteButton.setAttribute("disabled", "true");
      });
    }
  
  });
}

function markForm(e){
  let totalShownForms = document.querySelectorAll(`.repeatable-form:not([style*="display: none"])`).length;
  console.log("markForm start: " + totalShownForms)
  

  if (totalShownForms == 1) {
    // toggle the radio buttons
    let radioButton = document.querySelector('input[name="other_contacts-has_other_contacts"][value="False"]');
    radioButton.checked = true;

    // Trigger the change event
    let event = new Event('change');
    radioButton.dispatchEvent(event);
  } else {

    // Grab the hidden delete input and CHECK it
    let formToRemove = e.target.closest(".repeatable-form");
    if (formToRemove) {
      let deleteInput = formToRemove.querySelector('input[class="deletion"]');
      if (deleteInput) {
        deleteInput.value = 'on';
      }
    }

    // Set display to 'none'
    formToRemove.style.display = 'none';

    // update headers on shown forms
    console.log("markForm end: " + totalShownForms)

  }
  

  // let shownForms = document.querySelectorAll(".repeatable-form");
  // totalForms.setAttribute('value', `${forms.length}`);

  // let formNumberRegex = RegExp(`form-(\\d){1}-`, 'g');
  // let formLabelRegex = RegExp(`${formLabel} (\\d+){1}`, 'g');
  // // For the example on Nameservers
  // let formExampleRegex = RegExp(`ns(\\d+){1}`, 'g');

  // forms.forEach((form, index) => {
  //   // Iterate over child nodes of the current element
  //   Array.from(form.querySelectorAll('label, input, select')).forEach((node) => {
  //     // Iterate through the attributes of the current node
  //     Array.from(node.attributes).forEach((attr) => {
  //       // Check if the attribute value matches the regex
  //       if (formNumberRegex.test(attr.value)) {
  //         // Replace the attribute value with the updated value
  //         attr.value = attr.value.replace(formNumberRegex, `form-${index}-`);
  //       }
  //     });
  //   });

  //   // h2 and legend for DS form, label for nameservers  
  //   Array.from(form.querySelectorAll('h2, legend, label, p')).forEach((node) => {
      
  //     // If the node is a nameserver label, one of the first 2 which was previously 3 and up (not required)
  //     // inject the USWDS required markup and make sure the INPUT is required
  //     if (isNameserversForm && index <= 1 && node.innerHTML.includes('server') && !node.innerHTML.includes('*')) {
  //       // Create a new element
  //       const newElement = document.createElement('abbr');
  //       newElement.textContent = '*';
  //       newElement.setAttribute("title", "required");
  //       newElement.classList.add("usa-hint", "usa-hint--required");

  //       // Append the new element to the label
  //       node.appendChild(newElement);
  //       // Find the next sibling that is an input element
  //       let nextInputElement = node.nextElementSibling;

  //       while (nextInputElement) {
  //         if (nextInputElement.tagName === 'INPUT') {
  //           // Found the next input element
  //           nextInputElement.setAttribute("required", "")
  //           break;
  //         }
  //         nextInputElement = nextInputElement.nextElementSibling;
  //       }
  //       nextInputElement.required = true;
  //     }

  //     let innerSpan = node.querySelector('span')
  //     if (innerSpan) {
  //       innerSpan.textContent = innerSpan.textContent.replace(formLabelRegex, `${formLabel} ${index + 1}`);
  //     } else {
  //       node.textContent = node.textContent.replace(formLabelRegex, `${formLabel} ${index + 1}`);
  //       node.textContent = node.textContent.replace(formExampleRegex, `ns${index + 1}`);
  //     }
  //   });

  //   // Display the add more button if we have less than 13 forms
  //   if (isNameserversForm && forms.length <= 13) {
  //     console.log('remove disabled');
  //     addButton.removeAttribute("disabled");
  //   }

  //   if (isNameserversForm && forms.length < 3) {
  //     // Hide the delete buttons on the remaining nameservers
  //     Array.from(form.querySelectorAll('.delete-record')).forEach((deleteButton) => {
  //       deleteButton.setAttribute("disabled", "true");
  //     });
  //   }
  
  // });
}

function prepareNewDeleteButton(btn, formLabel) {
  let formIdentifier = "form"
  let isNameserversForm = document.title.includes("DNS name servers |");
  let isOtherContactsForm = document.title.includes("Other employees from your organization");
  let addButton = document.querySelector("#add-form");
  if (isOtherContactsForm) {
    formIdentifier = "other_contacts";
  }
  
  if (isOtherContactsForm) {
    // We will mark the forms for deletion
    btn.addEventListener('click', markForm);
  } else {
    // We will remove the forms and re-order the formset
    btn.addEventListener('click', function(e) {
      removeForm(e, formLabel, isNameserversForm, addButton, formIdentifier);
    });
  }
}

/**
 * Prepare the namerservers and DS data forms delete buttons
 * We will call this on the forms init, and also every time we add a form
 * 
 */
function prepareDeleteButtons(formLabel) {
  let formIdentifier = "form"
  let deleteButtons = document.querySelectorAll(".delete-record");
  let isNameserversForm = document.title.includes("DNS name servers |");
  let isOtherContactsForm = document.title.includes("Other employees from your organization");
  let addButton = document.querySelector("#add-form");
  if (isOtherContactsForm) {
    formIdentifier = "other_contacts";
  }
  

  // Loop through each delete button and attach the click event listener
  deleteButtons.forEach((deleteButton) => {
    if (isOtherContactsForm) {
      // We will mark the forms for deletion
      deleteButton.addEventListener('click', markForm);
    } else {
      // We will remove the forms and re-order the formset
      deleteButton.addEventListener('click', function(e) {
        removeForm(e, formLabel, isNameserversForm, addButton, formIdentifier);
      });
    }
  });

}

/**
 * On form load, hide deleted forms, ie. those forms with hidden input of class 'deletion'
 * with value='on'
 */
function hideDeletedForms() {
  let hiddenDeleteButtonsWithValueOn = document.querySelectorAll('input[type="hidden"].deletion[value="on"]');

  // Iterating over the NodeList of hidden inputs
  hiddenDeleteButtonsWithValueOn.forEach(function(hiddenInput) {
      // Finding the closest parent element with class "repeatable-form" for each hidden input
      var repeatableFormToHide = hiddenInput.closest('.repeatable-form');
  
      // Checking if a matching parent element is found for each hidden input
      if (repeatableFormToHide) {
          // Setting the display property to "none" for each matching parent element
          repeatableFormToHide.style.display = 'none';
      }
  });
}

/**
 * An IIFE that attaches a click handler for our dynamic formsets
 *
 * Only does something on a few pages, but it should be fast enough to run
 * it everywhere.
 */
(function prepareFormsetsForms() {
  let formIdentifier = "form"
  let repeatableForm = document.querySelectorAll(".repeatable-form");
  let container = document.querySelector("#form-container");
  let addButton = document.querySelector("#add-form");
  let cloneIndex = 0;
  let formLabel = '';
  let isNameserversForm = document.title.includes("DNS name servers |");
  let isOtherContactsForm = document.title.includes("Other employees from your organization");
  if (isNameserversForm) {
    cloneIndex = 2;
    formLabel = "Name server";
  } else if ((document.title.includes("DS Data |")) || (document.title.includes("Key Data |"))) {
    formLabel = "DS Data record";
  } else if (isOtherContactsForm) {
    formLabel = "Organization contact";
    container = document.querySelector("#other-employees");
    formIdentifier = "other_contacts"
  }
  let totalForms = document.querySelector(`#id_${formIdentifier}-TOTAL_FORMS`);

  // On load: Disable the add more button if we have 13 forms
  if (isNameserversForm && document.querySelectorAll(".repeatable-form").length == 13) {
    addButton.setAttribute("disabled", "true");
  }

  // Hide forms which have previously been deleted
  hideDeletedForms()

  // Attach click event listener on the delete buttons of the existing forms
  prepareDeleteButtons(formLabel);

  if (addButton)
    addButton.addEventListener('click', addForm);

  function addForm(e){
      let forms = document.querySelectorAll(".repeatable-form");
      let formNum = forms.length;
      let newForm = repeatableForm[cloneIndex].cloneNode(true);
      let formNumberRegex = RegExp(`${formIdentifier}-(\\d){1}-`,'g');
      let formLabelRegex = RegExp(`${formLabel} (\\d){1}`, 'g');
      // For the eample on Nameservers
      let formExampleRegex = RegExp(`ns(\\d){1}`, 'g');

      // Some Nameserver form checks since the delete can mess up the source object we're copying
      // in regards to required fields and hidden delete buttons
      if (isNameserversForm) {

        // If the source element we're copying has required on an input,
        // reset that input
        let formRequiredNeedsCleanUp = newForm.innerHTML.includes('*');
        if (formRequiredNeedsCleanUp) {
          newForm.querySelector('label abbr').remove();
          // Get all input elements within the container
          const inputElements = newForm.querySelectorAll("input");
          // Loop through each input element and remove the 'required' attribute
          inputElements.forEach((input) => {
            if (input.hasAttribute("required")) {
              input.removeAttribute("required");
            }
          });
        }

        // If the source element we're copying has an disabled delete button,
        // enable that button
        let deleteButton= newForm.querySelector('.delete-record');
        if (deleteButton.hasAttribute("disabled")) {
          deleteButton.removeAttribute("disabled");
        }
      }

      formNum++;

      newForm.innerHTML = newForm.innerHTML.replace(formNumberRegex, `${formIdentifier}-${formNum-1}-`);
      newForm.innerHTML = newForm.innerHTML.replace(formLabelRegex, `${formLabel} ${formNum}`);
      newForm.innerHTML = newForm.innerHTML.replace(formExampleRegex, `ns${formNum}`);
      container.insertBefore(newForm, addButton);

      newForm.style.display = 'block';

      let inputs = newForm.querySelectorAll("input");
      // Reset the values of each input to blank
      inputs.forEach((input) => {
        input.classList.remove("usa-input--error");
        if (input.type === "text" || input.type === "number" || input.type === "password" || input.type === "email" || input.type === "tel") {
          input.value = ""; // Set the value to an empty string
          
        } else if (input.type === "checkbox" || input.type === "radio") {
          input.checked = false; // Uncheck checkboxes and radios
        }
      });

      // Reset any existing validation classes
      let selects = newForm.querySelectorAll("select");
      selects.forEach((select) => {
        select.classList.remove("usa-input--error");
        select.selectedIndex = 0; // Set the value to an empty string
      });

      let labels = newForm.querySelectorAll("label");
      labels.forEach((label) => {
        label.classList.remove("usa-label--error");
      });

      let usaFormGroups = newForm.querySelectorAll(".usa-form-group");
      usaFormGroups.forEach((usaFormGroup) => {
        usaFormGroup.classList.remove("usa-form-group--error");
      });

      // Remove any existing error messages
      let usaErrorMessages = newForm.querySelectorAll(".usa-error-message");
      usaErrorMessages.forEach((usaErrorMessage) => {
        let parentDiv = usaErrorMessage.closest('div');
        if (parentDiv) {
          parentDiv.remove(); // Remove the parent div if it exists
        }
      });

      totalForms.setAttribute('value', `${formNum}`);

      // Attach click event listener on the delete buttons of the new form
      let newDeleteButton = newForm.querySelector(".delete-record");
      prepareNewDeleteButton(newDeleteButton, formLabel);

      // Disable the add more button if we have 13 forms
      if (isNameserversForm && formNum == 13) {
        addButton.setAttribute("disabled", "true");
      }

      if (isNameserversForm && forms.length >= 2) {
        // Enable the delete buttons on the nameservers
        forms.forEach((form, index) => {
          Array.from(form.querySelectorAll('.delete-record')).forEach((deleteButton) => {
            deleteButton.removeAttribute("disabled");
          });
        });
      }
  }
})();

/**
 * An IIFE that triggers a modal on the DS Data Form under certain conditions
 *
 */
(function triggerModalOnDsDataForm() {
  let saveButon = document.querySelector("#save-ds-data");

  // The view context will cause a hitherto hidden modal trigger to
  // show up. On save, we'll test for that modal trigger appearing. We'll
  // run that test once every 100 ms for 5 secs, which should balance performance
  // while accounting for network or lag issues.
  if (saveButon) {
    let i = 0;
    var tryToTriggerModal = setInterval(function() {
        i++;
        if (i > 100) {
          clearInterval(tryToTriggerModal);
        }
        let modalTrigger = document.querySelector("#ds-toggle-dnssec-alert");
        if (modalTrigger) {
          modalTrigger.click()
          clearInterval(tryToTriggerModal);
        }
    }, 50);
  }
})();

function toggleTwoDomElements(ele1, ele2, index) {
  let element1 = document.getElementById(ele1);
  let element2 = document.getElementById(ele2);
  if (element1 && element2) {
      // Toggle display based on the index
      element1.style.display = index === 1 ? 'block' : 'none';
      element2.style.display = index === 2 ? 'block' : 'none';
  } else {
      console.error('One or both elements not found.');
  }
}

/**
 * An IIFE that listens to the other contacts radio form on DAs and toggles the contacts/no other contacts forms 
 *
 */
(function otherContactsFormListener() {
  // Get the radio buttons
  let radioButtons = document.querySelectorAll('input[name="other_contacts-has_other_contacts"]');

  function handleRadioButtonChange() {
    // Check the value of the selected radio button
    // Attempt to find the radio button element that is checked
    let radioButtonChecked = document.querySelector('input[name="other_contacts-has_other_contacts"]:checked');

    // Check if the element exists before accessing its value
    let selectedValue = radioButtonChecked ? radioButtonChecked.value : null;

    switch (selectedValue) {
      case 'True':
        toggleTwoDomElements('other-employees', 'no-other-employees', 1);
        break;

      case 'False':
        toggleTwoDomElements('other-employees', 'no-other-employees', 2);
        break;

      default:
        toggleTwoDomElements('other-employees', 'no-other-employees', 0);
    }
  }

  if (radioButtons.length) {
    // Add event listener to each radio button
    radioButtons.forEach(function (radioButton) {
      radioButton.addEventListener('change', handleRadioButtonChange);
    });

    // initialize
    handleRadioButtonChange();
  }
})();

