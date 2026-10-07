# Goodbye{% extends %}{% block %}{% include %}{% custom_tag %}

Hello<c-comp />

## Bringing component-based design to django templates

## Before: Strongly Coupled, Verbose

view.html

product_layout.html

```xml
{% extends "product_layout.html" %}

{% block img_url %}
icon.png
{% endblock %}

{% block title %}
Item Title
{% endblock %}

{% block content %}
    Description of the product

    {% block price %}
    $10
    {% endblock %}
{% endblock %}
```

## After: Decoupled, Clean & Re-usable

view.html

product.html

```xml
<c-product img_url="icon.png"
    title="Item Title"
    price="$10">
    Description of the product
</c-product>
```

### Why cotton?

Rapid UI composition

Efficiently compose and reuse UI components. Adopting a modular design system streamlines workflow and boosts productivity.

Harmonious with Tailwind CSS

Tailwind's utility-first approach compliments component based design - isolating style in re-usable components, enhancing maintainability.

{%

Interoperable with Django Templates

Cotton enhances Django templates without replacing them, allowing progressive enhancement while maintaining full use of existing template features.

Enhanced Productivity

Cotton's HTML tag-like syntax allows code editors to recognize its components as HTML elements, enabling features like syntax highlighting and automatic tag completion.

Minimal Overhead

Cotton compiles to native django components and the compilation step is automatically cached and dynamically managed.


## Install cotton

Run the following command:

```python
pipenv install django-cotton
```

Then update your settings.py:

### For automatic configuration:

settings.py

```python
INSTALLED_APPS = [
    'django_cotton',
]
```

This will attempt to automatically handle the settings.py by adding the required loader and templatetags.

### For custom configuration

If your project requires any non-default loaders or you do not wish Cotton to manage your settings, you should instead provide `django_cotton.apps.SimpleAppConfig` in your INSTALLED_APPS:

settings.py

```python
INSTALLED_APPS = [
    'django_cotton.apps.SimpleAppConfig',
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        ...
        "OPTIONS": {
            "loaders": [(
                "django.template.loaders.cached.Loader",
                [
                    "django_cotton.cotton_loader.Loader",
                    "django.template.loaders.filesystem.Loader",
                    "django.template.loaders.app_directories.Loader",
                ],
            )],
            "builtins": [
                "django_cotton.templatetags.cotton"
            ],
        }
    }
]
```

## Create a component

Create a new directory in your templates directory called cotton. Inside this directory create a new file called card.html with the following content:

templates/cotton/card.html

```xml
<div class="bg-white shadow rounded border p-4">
    <h2>{{ title }}</h2>
    <p>{{ slot }}</p>
    <button href="{% url url %}">Read more</button>
</div>
```

## Templates location

Cotton supports 2 common approaches regarding the location of the `templates` directory:

- **App level** - You can place your cotton folder in any of your installed app folders, like:
    
    `[project]/[app]/templates/cotton/row.html`
    
- **Project root** - You can place your cotton folder in a project level templates directory, like:
    
    `[project]/templates/cotton/row.html`
    
    (`[project]` location is provided by `BASE_DIR` if present or you may set it with `COTTON_BASE_DIR`)

Any style will allow you to include your component the same way: `<c-row />`

## Include a component

views.py

```python
def dashboard_view(request):
    return render(request, "dashboard.html")
```

templates/dashboard.html

```xml
<c-card title="Trees" url="trees">
    We have the best trees
</c-card>

<c-card title="Spades" url="spades">
    The best spades in the land
</c-card>
```


## Install cotton

Run the following command:

```python
pip install django-cotton
```

Then update your settings.py:

### For automatic configuration:

settings.py

```python
INSTALLED_APPS = [
    'django_cotton',
]
```

This will attempt to automatically handle the settings.py by adding the required loader and templatetags.

### For custom configuration

If your project requires any non-default loaders or you do not wish Cotton to manage your settings, you should instead provide `django_cotton.apps.SimpleAppConfig` in your INSTALLED_APPS:

settings.py

```python
INSTALLED_APPS = [
    'django_cotton.apps.SimpleAppConfig',
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        ...
        "OPTIONS": {
            "loaders": [(
                "django.template.loaders.cached.Loader",
                [
                    "django_cotton.cotton_loader.Loader",
                    "django.template.loaders.filesystem.Loader",
                    "django.template.loaders.app_directories.Loader",
                ],
            )],
            "builtins": [
                "django_cotton.templatetags.cotton"
            ],
        }
    }
]
```

## Create a component

Create a new directory in your templates directory called cotton. Inside this directory create a new file called card.html with the following content:

templates/cotton/card.html

```xml
<div class="bg-white shadow rounded border p-4">
    <h2>{{ title }}</h2>
    <p>{{ slot }}</p>
    <button href="{% url url %}">Read more</button>
</div>
```

## Templates location

Cotton supports 2 common approaches regarding the location of the `templates` directory:

- **App level** - You can place your cotton folder in any of your installed app folders, like:
    
    `[project]/[app]/templates/cotton/row.html`
    
- **Project root** - You can place your cotton folder in a project level templates directory, like:
    
    `[project]/templates/cotton/row.html`
    
    (`[project]` location is provided by `BASE_DIR` if present or you may set it with `COTTON_BASE_DIR`)

Any style will allow you to include your component the same way: `<c-row />`

## Include a component

views.py

```python
def dashboard_view(request):
    return render(request, "dashboard.html")
```

templates/dashboard.html

```xml
<c-card title="Trees" url="trees">
    We have the best trees
</c-card>

<c-card title="Spades" url="spades">
    The best spades in the land
</c-card>
```


# Usage Patterns

### Basics

- Cotton components should be placed in the templates/cotton folder ('cotton' path is [configurable](https://django-cotton.com/docs/configuration) using `COTTON_DIR`).
- The `templates` folder can be located in either an app-level or top-level project root folder.

### Naming

Cotton uses the following naming conventions:

- By default, component file names are in snake_case (my_component.html).
- kebab-case filenames (my-component.html) can be enabled with `COTTON_SNAKE_CASED_NAMES = False` see [configuration](https://django-cotton.com/docs/configuration).
- Components are included in templates using kebab-case name of the component: `<c-my-component />`

### Subfolders

- Components in subfolders can be called using dot notation to represent folder levels.
- A component in sidebar/menu/link.html would be included with `<c-sidebar.menu.link />`

### The index.html component

When your component has sub-components, you can define the default component of a folder by adding an `index.html`. This helps to keep your project structure tidy and reduce additional code in the template.

Project structure

```xml
templates/
├── cotton/
│   ├── card/
│   │   ├── index.html
│   │   ├── header.html
```

Usage

```xml
<c-card>
    <c-card.header>...</c-card.header>
</c-card>
```

### Tag Style

- Components can either be self-closing `<c-my-component />` or have a closing tag `<c-my-component></c-my-component>`

### Attribute Proxying Pattern

The `:attrs` dynamic attribute enables us to create wrapper components that proxy all their attributes to an inner component:

view.html

```xml
<c-outer
    class="outer-class"
    :count="42"
    :enabled="False">
    Content passed to inner component
</c-outer>
```

cotton/outer.html

```xml
<c-inner :attrs="attrs">{{ slot }}</c-inner>
```

cotton/inner.html

```xml
{{ class }}     <!-- "outer-class" -->
{{ count }}     <!-- 42 -->
{{ enabled }}   <!-- False -->
{{ slot }}      <!-- Content passed to inner component -->
```

The attributes are passed through to the inner component with their original types preserved (strings, numbers, booleans, lists, etc.), making this pattern ideal for creating higher-order components.

This pattern is particularly useful for Django form fields, where you might create a component hierarchy that passes Django widget attributes through multiple layers while adding labels, error handling, and styling at each level.


# Building a re-usable form input field

Componentizing form fields enable you to easily maintain a consistent style across your whole app. This approach is particularly favourable when using a utility first CSS design system like Tailwind where every aspect of the style is detailed and maintained in isolated component files.

For this example, we're using Tailwind for styling. Let's start with a standard input:

form_view.html

```xml
<input type="text" name="shoe_size" placeholder="Shoe Size" class="border rounded shadow px-3 py-1.5">
```

preview

Having to repeat this code more than once may get tedious and difficult to maintain. Let's componentize.

cotton/input.html

```xml
<input type="text" name="{{ name }}" placeholder="{{ placeholder }}" class="border rounded shadow px-3 py-1.5">
```

form_view.html

```xml
<c-input name="shoe_size" placeholder="Show Size" />
<c-input name="country" placeholder="Country" />
<c-input name="age" placeholder="Age" />
```

preview

## Change the input type

You will probably need more than just a text input in your project. So let's declare an attribute `text` in `<c-vars />`. Adding it as a var will allow us to set "text" as the default. Additionally, it will be excluded from `{{ attrs }}`:

cotton/input.html

```xml
<c-vars type="text" />

<input type="{{ type }}" {{ attrs }} class="border rounded shadow px-3 py-1.5">
```

form_view.html

```xml
<c-input name="some_text" placeholder="Just a text field" />
<c-input type="email" name="email" placeholder="Email" />
<c-input type="password" name="password" placeholder="Password" />
<c-input type="number" name="Count" placeholder="Password" />
```

preview

## Adding validation state

Let's also handle displaying errors when we need to.

cotton/input.html

```xml
<c-vars type="text" errors />

<input type="{{ type }}" {{ attrs }} class="border rounded shadow px-3 py-1.5 {% if errors %}border-red-500{% endif %}">

{% if errors %}
    <div class="text-red-500 text-sm mt-1">{{ errors.as_text }}</div>
{% endif %}
```

form_view.html

```xml
<c-input name="surname" placeholder="Surname" :errors="form.surname.errors" />
```

preview

Your surname is required.

## Bonus - Adding icons

To take customization a step further and to demonstrate the flexibility of cotton, let's now give our input component the ability to display icons.

cotton/input.html

```xml
<c-vars type="text" leading_icon trailing_icon />

<div class="border rounded shadow flex items-center">
    {% if leading_icon %}
        <div class="pl-3">{{ leading_icon }}</div>
    {% endif %}

    <input type="{{ type }}" {{ attrs }} class="px-3 py-1.5 w-full">
</div>
```

form_view.html

```xml
<c-input name="text" name="username" placeholder="Username">
    <c-slot name="leading_icon">
        <svg>...</svg>
    </c-slot>
</c-input>

<c-input type="password" name="password" name="password" placeholder="Password">
    <c-slot name="leading_icon">
        <svg>...</svg>
    </c-slot>
</c-input>
```

# Re-usable tabs with alpine.js

Be sure to checkout the notes on alpine.js support [here](https://django-cotton.com/docs/components#alpine-js-support).

Let's tackle together a common UI requirement - tabs.

### We'll start by defining some goals:

- A tab component should be re-usable
- The usage should be simple, keeping markup to a minimum
- It should be able to contain any number of tabs
- It should indicate the active tab

## Start with a static prototype

Before we think about components and adding interactivity, we'll create the design in HTML and Tailwind CSS. This way we can make sure we're happy with the overall look and design.

Static example

```xml
<div class="bg-white rounded-lg overflow-hidden border shadow">

    <!-- the navigation for the tabs -->
    <div class="flex items-center space-x-5 w-full bg-gray-100">
        <div class="px-5 py-3 cursor-pointer bg-white text-teal-500">
            Tab 1
        </div>
        <div class="px-5 py-3 cursor-pointer border-b-[3px] border-b-transparent">
            Tab 2
        </div>
    </div>

    <!-- tab's content will go here -->
    <div class="px-5 py-2">
        <p>Lorem ipsum ...</p>
    </div>
</div>
```

preview

Tab 1

Tab 2

Lorem ipsum ...

## Preparing cotton components

Now we have the design right, let's chop it up into components.

### <c-tabs /> component

cotton/tabs.html

```xml
<div class="bg-white rounded-lg overflow-hidden border shadow">
    <div class="flex items-center space-x-5 w-full bg-gray-100">
        <!-- tab navigation will go here -->
    </div>

    <div class="px-5 py-2">
        <!-- tab content will go here -->
        {{ slot }}
    </div>
</div>
```

### <c-tab /> component

cotton/tab.html

```xml
<div>
    {{ slot }}
</div>
```

This will give us the ability to initiate a set of tabs using markup like:

```xml
<c-tabs>
    <c-tab>Content for tab 1</c-tab>
    <c-tab>Content for tab 2</c-tab>
    <c-tab>Content for tab 3</c-tab>
</c-tabs>
```

## Adding interactivity

Up to this point, we still don't have a working tabs component. We'll join up the dots now and pull in alpine.js, a lightweight javascript library designed to assist in front end interactions. Follow the [installation guide](https://alpinejs.dev/essentials/installation) before continuing.

### Add an Alpine data component

In alpine you can define re-usable data functions. Place this code somewhere globally in your project.

```xml
<!-- Place this in somewhere like base layout of your app -->
<script>
    document.addEventListener('alpine:init', () => {
        Alpine.data('tabs', () => ({
            tabs: [],
            currentTab: null,
            isCurrent(tab) {
                return this.currentTab === tab
            },
            register(name) {
                this.tabs.push(name)
            }
        }))
    })
</script>
```

### Modifying tabs.html

Next we'll make the appropriate changes to our tabs.html component to integrate alpine.js

```xml
<div x-data="tabs" x-init="$watch('tabs', () => currentTab = tabs[0])" class="...">
    <!-- The $watch function will set the first tab as the active tab. -->
    <div class="...">
        <template x-for="tab in tabs">
            <div @click="currentTab = tab" x-text="tab" class="..." :class="currentTab === tab ? 'text-teal-600 font-semibold bg-white' : 'text-gray-500'"></div>
            <!-- Here, we dynamically create the tab navigation items based on the child 'tabs' that are registered. -->
        </template>
    </div>

    <div class="px-5 py-2">
        {{ slot }}
        <!-- All of the <c-tab /> items will go here. -->
    </div>
</div>
```

### Modifying tab.html

We now need to modify the tab component so that it is registered each time it is imported into the dom.

```xml
<div x-data x-show="isCurrent('{{ name }}')" x-init="register('{{ name }}')">
    {{ slot }}
</div>
```

## Usage and example

We have now built a re-usable tab component that satisfies all of our initial goals.

```xml
<c-tabs>
    <c-tab name="Tab 1">Tab 1 content</c-tab>
    <c-tab name="Tab 2">Tab 2 content</c-tab>
    <c-tab name="Tab 3">Tab 3 content</c-tab>
</c-tabs>
```

# Re-usable tabs with alpine.js

Be sure to checkout the notes on alpine.js support [here](https://django-cotton.com/docs/components#alpine-js-support).

Let's tackle together a common UI requirement - tabs.

### We'll start by defining some goals:

- A tab component should be re-usable
- The usage should be simple, keeping markup to a minimum
- It should be able to contain any number of tabs
- It should indicate the active tab

## Start with a static prototype

Before we think about components and adding interactivity, we'll create the design in HTML and Tailwind CSS. This way we can make sure we're happy with the overall look and design.

Static example

```xml
<div class="bg-white rounded-lg overflow-hidden border shadow">

    <!-- the navigation for the tabs -->
    <div class="flex items-center space-x-5 w-full bg-gray-100">
        <div class="px-5 py-3 cursor-pointer bg-white text-teal-500">
            Tab 1
        </div>
        <div class="px-5 py-3 cursor-pointer border-b-[3px] border-b-transparent">
            Tab 2
        </div>
    </div>

    <!-- tab's content will go here -->
    <div class="px-5 py-2">
        <p>Lorem ipsum ...</p>
    </div>
</div>
```

preview

Tab 1

Tab 2

Lorem ipsum ...

## Preparing cotton components

Now we have the design right, let's chop it up into components.

### <c-tabs /> component

cotton/tabs.html

```xml
<div class="bg-white rounded-lg overflow-hidden border shadow">
    <div class="flex items-center space-x-5 w-full bg-gray-100">
        <!-- tab navigation will go here -->
    </div>

    <div class="px-5 py-2">
        <!-- tab content will go here -->
        {{ slot }}
    </div>
</div>
```

### <c-tab /> component

cotton/tab.html

```xml
<div>
    {{ slot }}
</div>
```

This will give us the ability to initiate a set of tabs using markup like:

```xml
<c-tabs>
    <c-tab>Content for tab 1</c-tab>
    <c-tab>Content for tab 2</c-tab>
    <c-tab>Content for tab 3</c-tab>
</c-tabs>
```

## Adding interactivity

Up to this point, we still don't have a working tabs component. We'll join up the dots now and pull in alpine.js, a lightweight javascript library designed to assist in front end interactions. Follow the [installation guide](https://alpinejs.dev/essentials/installation) before continuing.

### Add an Alpine data component

In alpine you can define re-usable data functions. Place this code somewhere globally in your project.

```xml
<!-- Place this in somewhere like base layout of your app -->
<script>
    document.addEventListener('alpine:init', () => {
        Alpine.data('tabs', () => ({
            tabs: [],
            currentTab: null,
            isCurrent(tab) {
                return this.currentTab === tab
            },
            register(name) {
                this.tabs.push(name)
            }
        }))
    })
</script>
```

### Modifying tabs.html

Next we'll make the appropriate changes to our tabs.html component to integrate alpine.js

```xml
<div x-data="tabs" x-init="$watch('tabs', () => currentTab = tabs[0])" class="...">
    <!-- The $watch function will set the first tab as the active tab. -->
    <div class="...">
        <template x-for="tab in tabs">
            <div @click="currentTab = tab" x-text="tab" class="..." :class="currentTab === tab ? 'text-teal-600 font-semibold bg-white' : 'text-gray-500'"></div>
            <!-- Here, we dynamically create the tab navigation items based on the child 'tabs' that are registered. -->
        </template>
    </div>

    <div class="px-5 py-2">
        {{ slot }}
        <!-- All of the <c-tab /> items will go here. -->
    </div>
</div>
```

### Modifying tab.html

We now need to modify the tab component so that it is registered each time it is imported into the dom.

```xml
<div x-data x-show="isCurrent('{{ name }}')" x-init="register('{{ name }}')">
    {{ slot }}
</div>
```

## Usage and example

We have now built a re-usable tab component that satisfies all of our initial goals.

```xml
<c-tabs>
    <c-tab name="Tab 1">Tab 1 content</c-tab>
    <c-tab name="Tab 2">Tab 2 content</c-tab>
    <c-tab name="Tab 3">Tab 3 content</c-tab>
</c-tabs>
```

# Re-usable tabs with alpine.js

Be sure to checkout the notes on alpine.js support [here](https://django-cotton.com/docs/components#alpine-js-support).

Let's tackle together a common UI requirement - tabs.

### We'll start by defining some goals:

- A tab component should be re-usable
- The usage should be simple, keeping markup to a minimum
- It should be able to contain any number of tabs
- It should indicate the active tab

## Start with a static prototype

Before we think about components and adding interactivity, we'll create the design in HTML and Tailwind CSS. This way we can make sure we're happy with the overall look and design.

Static example

```xml
<div class="bg-white rounded-lg overflow-hidden border shadow">

    <!-- the navigation for the tabs -->
    <div class="flex items-center space-x-5 w-full bg-gray-100">
        <div class="px-5 py-3 cursor-pointer bg-white text-teal-500">
            Tab 1
        </div>
        <div class="px-5 py-3 cursor-pointer border-b-[3px] border-b-transparent">
            Tab 2
        </div>
    </div>

    <!-- tab's content will go here -->
    <div class="px-5 py-2">
        <p>Lorem ipsum ...</p>
    </div>
</div>
```

preview

Tab 1

Tab 2

Lorem ipsum ...

## Preparing cotton components

Now we have the design right, let's chop it up into components.

### <c-tabs /> component

cotton/tabs.html

```xml
<div class="bg-white rounded-lg overflow-hidden border shadow">
    <div class="flex items-center space-x-5 w-full bg-gray-100">
        <!-- tab navigation will go here -->
    </div>

    <div class="px-5 py-2">
        <!-- tab content will go here -->
        {{ slot }}
    </div>
</div>
```

### <c-tab /> component

cotton/tab.html

```xml
<div>
    {{ slot }}
</div>
```

This will give us the ability to initiate a set of tabs using markup like:

```xml
<c-tabs>
    <c-tab>Content for tab 1</c-tab>
    <c-tab>Content for tab 2</c-tab>
    <c-tab>Content for tab 3</c-tab>
</c-tabs>
```

## Adding interactivity

Up to this point, we still don't have a working tabs component. We'll join up the dots now and pull in alpine.js, a lightweight javascript library designed to assist in front end interactions. Follow the [installation guide](https://alpinejs.dev/essentials/installation) before continuing.

### Add an Alpine data component

In alpine you can define re-usable data functions. Place this code somewhere globally in your project.

```xml
<!-- Place this in somewhere like base layout of your app -->
<script>
    document.addEventListener('alpine:init', () => {
        Alpine.data('tabs', () => ({
            tabs: [],
            currentTab: null,
            isCurrent(tab) {
                return this.currentTab === tab
            },
            register(name) {
                this.tabs.push(name)
            }
        }))
    })
</script>
```

### Modifying tabs.html

Next we'll make the appropriate changes to our tabs.html component to integrate alpine.js

```xml
<div x-data="tabs" x-init="$watch('tabs', () => currentTab = tabs[0])" class="...">
    <!-- The $watch function will set the first tab as the active tab. -->
    <div class="...">
        <template x-for="tab in tabs">
            <div @click="currentTab = tab" x-text="tab" class="..." :class="currentTab === tab ? 'text-teal-600 font-semibold bg-white' : 'text-gray-500'"></div>
            <!-- Here, we dynamically create the tab navigation items based on the child 'tabs' that are registered. -->
        </template>
    </div>

    <div class="px-5 py-2">
        {{ slot }}
        <!-- All of the <c-tab /> items will go here. -->
    </div>
</div>
```

### Modifying tab.html

We now need to modify the tab component so that it is registered each time it is imported into the dom.

```xml
<div x-data x-show="isCurrent('{{ name }}')" x-init="register('{{ name }}')">
    {{ slot }}
</div>
```

## Usage and example

We have now built a re-usable tab component that satisfies all of our initial goals.

```xml
<c-tabs>
    <c-tab name="Tab 1">Tab 1 content</c-tab>
    <c-tab name="Tab 2">Tab 2 content</c-tab>
    <c-tab name="Tab 3">Tab 3 content</c-tab>
</c-tabs>
```

# Layouts

Cottons makes building layouts a piece of cake. Let's start with composing a base layout that contains the base of our view:

cotton/layouts/base.html

```xml
<html>
    <head>
        ...
    </head>
    <body>
        {{ slot }}
    </body>
</html>
```

## Create layout variants

Imagine that we're creating a web app with an authenticated area, so we'll need areas for guests and users. Let's create these, extending from the base component.

cotton/layouts/guest.html

```xml
<c-layouts.base>
    {{ slot }}
</c-layouts.base>
```

cotton/layouts/app.html

```xml
<c-layouts.base>
    <div class="sidebar">
        {{ sidebar }}
    </div>

    <div class="main">
        {{ slot }}
    </div>
</c-layouts.base>
```

## Using the layouts

login.html

```xml
<c-layouts.guest>
    <div id="loginForm">
        <input name="email" type="email" placeholder="Email">
        ...
    </div>
</c-layouts.guest>
```

dashboard.html

```xml
<c-layouts.app>
    <c-slot name="sidebar">
        <a href="/dashboard">Dashboard</a>
        ...
    </c-slot>
    <div id="dashboard">
        ...
    </div>
</c-layouts.app>
```
# Icons & SVG Graphics

Cotton's component-ized approach provides another compelling use-case. Sure, there are svg icon packages for Django already, but what if you need to use a custom icon in your project?

plane.svg

```xml
<svg viewBox="0 0 512 512">
  <g fill="none" stroke="#000" stroke-width="30" stroke-linejoin="round">
    <path d="M143.533 256 79.267 384.533v-192.8L497 127.467z"/>
    <path d="M143.533 256 79.267 384.533l119.352-73.448zM15 127.467h482L79.267 191.733z"/>
    <path d="M143.533 256 497 127.467l-241 241z"/>
  </g>
</svg>
```

preview

## Let's "cotton-ize"

cotton/icons/plane.html

```xml
<c-vars stroke_width="30" />

<svg {{ attrs }} viewBox="0 0 512 512">
  <g fill="none" stroke="currentColor" stroke-width="{{ stroke_width }}" stroke-linejoin="round">
    <path d="M143.533 256 79.267 384.533v-192.8L497 127.467z"/>
    <path d="M143.533 256 79.267 384.533l119.352-73.448zM15 127.467h482L79.267 191.733z"/>
    <path d="M143.533 256 497 127.467l-241 241z"/>
  </g>
</svg>
```

view.html

```xml
<c-icons.plane class="size-20 text-red-500" />
<c-icons.plane class="size-20 text-teal-500" />
<c-icons.plane class="size-20 text-gray-500 animate-bounce" />
<c-icons.plane class="size-24 text-purple-500" stroke_width="10" />
```

# Configuration

The following configuration can be provided in your `settings.py`:

`COTTON_DIR`

str (default: 'cotton')

Change the default path in your templates directory where cotton components can be placed, for example "components".

`COTTON_BASE_DIR`

str (default: None)

The base directory where - in addition to the app folders - cotton will search for the "templates" directory (see above). If not set, the `BASE_DIR` generated by `django-admin startproject` is used as a fallback, if it exists.

`COTTON_SNAKE_CASED_NAMES`

bool (default: True)

By default cotton will look for snake case versions of your component names. To turn this behaviour off (useful if you want to permit hyphenated filenames) then set this key to `False`.

###### Example:

`<c-my-button />`

###### As `True` (default)

Filepath: `cotton/my_button.html`

###### As `False`

Filepath: `cotton/my-button.html`