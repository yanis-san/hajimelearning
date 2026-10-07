
# Start Here

Create a blank HTML file somewhere on your computer with a name like: `i-love-alpine.html`

Using a text editor, fill the file with these contents:

```
<html><head>    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script></head><body>    <h1 x-data="{ message: 'I ❤️ Alpine' }" x-text="message"></h1></body></html>
```

Open your file in a web browser, if you see `I ❤️ Alpine`, you're ready to rumble!

Now that you're all set up to play around, let's look at three practical examples as a foundation for teaching you the basics of Alpine. By the end of this exercise, you should be more than equipped to start building stuff on your own. Let's goooooo.

- [Building a counter](https://alpinejs.dev/start-here#building-a-counter)
- [Building a dropdown](https://alpinejs.dev/start-here#building-a-dropdown)
- [Building a search Input](https://alpinejs.dev/start-here#building-a-search-input)

## [Building a counter](https://alpinejs.dev/start-here#building-a-counter)

Let's start with a simple "counter" component to demonstrate the basics of state and event listening in Alpine, two core features.

Insert the following into the `<body>` tag:

```
<div x-data="{ count: 0 }">    <button x-on:click="count++">Increment</button>     <span x-text="count"></span></div>
```

Increment 0

Now, you can see with 3 bits of Alpine sprinkled into this HTML, we've created an interactive "counter" component.

Let's walk through what's happening briefly:

### [Declaring data](https://alpinejs.dev/start-here#declaring-data)

```
<div x-data="{ count: 0 }">
```

Everything in Alpine starts with an `x-data` directive. Inside of `x-data`, in plain JavaScript, you declare an object of data that Alpine will track.

Every property inside this object will be made available to other directives inside this HTML element. In addition, when one of these properties changes, everything that relies on it will change as well.

> `x-data` is required on a parent element for most Alpine directives to work.

[→ Read more about `x-data`](https://alpinejs.dev/directives/data)

Let's look at `x-on` and see how it can access and modify the `count` property from above:

### [Listening for events](https://alpinejs.dev/start-here#listening-for-events)

```
<button x-on:click="count++">Increment</button>
```

`x-on` is a directive you can use to listen for any event on an element. We're listening for a `click` event in this case, so ours looks like `x-on:click`.

You can listen for other events as you'd imagine. For example, listening for a `mouseenter` event would look like this: `x-on:mouseenter`.

When a `click` event happens, Alpine will call the associated JavaScript expression, `count++` in our case. As you can see, we have direct access to data declared in the `x-data` expression.

> You will often see `@` instead of `x-on:`. This is a shorter, friendlier syntax that many prefer. From now on, this documentation will likely use `@` instead of `x-on:`.

[→ Read more about `x-on`](https://alpinejs.dev/directives/on)

### [Reacting to changes](https://alpinejs.dev/start-here#reacting-to-changes)

```
<span x-text="count"></span>
```

`x-text` is an Alpine directive you can use to set the text content of an element to the result of a JavaScript expression.

In this case, we're telling Alpine to always make sure that the contents of this `span` tag reflect the value of the `count` property.

In case it's not clear, `x-text`, like most directives accepts a plain JavaScript expression as an argument. So for example, you could instead set its contents to: `x-text="count * 2"` and the text content of the `span` will now always be 2 times the value of `count`.

[→ Read more about `x-text`](https://alpinejs.dev/directives/text)

## [Building a dropdown](https://alpinejs.dev/start-here#building-a-dropdown)

Now that we've seen some basic functionality, let's keep going and look at an important directive in Alpine: `x-show`, by building a contrived "dropdown" component.

Insert the following code into the `<body>` tag:

```
<div x-data="{ open: false }">    <button @click="open = ! open">Toggle</button>     <div x-show="open" @click.outside="open = false">Contents...</div></div>
```

Toggle

If you load this component, you should see that the "Contents..." are hidden by default. You can toggle showing them on the page by clicking the "Toggle" button.

The `x-data` and `x-on` directives should be familiar to you from the previous example, so we'll skip those explanations.

### [Toggling elements](https://alpinejs.dev/start-here#toggling-elements)

```
<div x-show="open" ...>Contents...</div>
```

`x-show` is an extremely powerful directive in Alpine that can be used to show and hide a block of HTML on a page based on the result of a JavaScript expression, in our case: `open`.

[→ Read more about `x-show`](https://alpinejs.dev/directives/show)

### [Listening for a click outside](https://alpinejs.dev/start-here#listening-for-a-click-outside)

```
<div ... @click.outside="open = false">Contents...</div>
```

You'll notice something new in this example: `.outside`. Many directives in Alpine accept "modifiers" that are chained onto the end of the directive and are separated by periods.

In this case, `.outside` tells Alpine to instead of listening for a click INSIDE the `<div>`, to listen for the click only if it happens OUTSIDE the `<div>`.

This is a convenience helper built into Alpine because this is a common need and implementing it by hand is annoying and complex.

[→ Read more about `x-on` modifiers](https://alpinejs.dev/directives/on#modifiers)

## [Building a search input](https://alpinejs.dev/start-here#building-a-search-input)

Let's now build a more complex component and introduce a handful of other directives and patterns.

Insert the following code into the `<body>` tag:

```
<div    x-data="{        search: '',         items: ['foo', 'bar', 'baz'],         get filteredItems() {            return this.items.filter(                i => i.startsWith(this.search)            )        }    }">    <input x-model="search" placeholder="Search...">     <ul>        <template x-for="item in filteredItems" :key="item">            <li x-text="item"></li>        </template>    </ul></div>
```

- foo
- bar
- baz

By default, all of the "items" (foo, bar, and baz) will be shown on the page, but you can filter them by typing into the text input. As you type, the list of items will change to reflect what you're searching for.

Now there's quite a bit happening here, so let's go through this snippet piece by piece.

### [Multi line formatting](https://alpinejs.dev/start-here#multi-line-formatting)

The first thing I'd like to point out is that `x-data` now has a lot more going on in it than before. To make it easier to write and read, we've split it up into multiple lines in our HTML. This is completely optional and we'll talk more in a bit about how to avoid this problem altogether, but for now, we'll keep all of this JavaScript directly in the HTML.

### [Binding to inputs](https://alpinejs.dev/start-here#binding-to-inputs)

```
<input x-model="search" placeholder="Search...">
```

You'll notice a new directive we haven't seen yet: `x-model`.

`x-model` is used to "bind" the value of an input element with a data property: "search" from `x-data="{ search: '', ... }"` in our case.

This means that anytime the value of the input changes, the value of "search" will change to reflect that.

`x-model` is capable of much more than this simple example.

[→ Read more about `x-model`](https://alpinejs.dev/directives/model)

### [Computed properties using getters](https://alpinejs.dev/start-here#computed-properties-using-getters)

The next bit I'd like to draw your attention to is the `items` and `filteredItems` properties from the `x-data` directive.

```
{    ...    items: ['foo', 'bar', 'baz'],     get filteredItems() {        return this.items.filter(            i => i.startsWith(this.search)        )    }}
```

The `items` property should be self-explanatory. Here we are setting the value of `items` to a JavaScript array of 3 different items (foo, bar, and baz).

The interesting part of this snippet is the `filteredItems` property.

Denoted by the `get` prefix for this property, `filteredItems` is a "getter" property in this object. This means we can access `filteredItems` as if it was a normal property in our data object, but when we do, JavaScript will evaluate the provided function under the hood and return the result.

It's completely acceptable to forgo the `get` and just make this a method that you can call from the template, but some prefer the nicer syntax of the getter.

[→ Read more about JavaScript getters](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/get)

Now let's look inside the `filteredItems` getter and make sure we understand what's going on there:

```
return this.items.filter(    i => i.startsWith(this.search))
```

This is all plain JavaScript. We are first getting the array of items (foo, bar, and baz) and filtering them using the provided callback: `i => i.startsWith(this.search)`.

By passing in this callback to `filter`, we are telling JavaScript to only return the items that start with the string: `this.search`, which like we saw with `x-model` will always reflect the value of the input.

You may notice that up until now, we haven't had to use `this.` to reference properties. However, because we are working directly inside the `x-data` object, we must reference any properties using `this.[property]` instead of simply `[property]`.

Because Alpine is a "reactive" framework. Any time the value of `this.search` changes, parts of the template that use `filteredItems` will automatically be updated.

### [Looping elements](https://alpinejs.dev/start-here#looping-elements)

Now that we understand the data part of our component, let's understand what's happening in the template that allows us to loop through `filteredItems` on the page.

```
<ul>    <template x-for="item in filteredItems">        <li x-text="item"></li>    </template></ul>
```

The first thing to notice here is the `x-for` directive. `x-for` expressions take the following form: `[item] in [items]` where [items] is any array of data, and [item] is the name of the variable that will be assigned to an iteration inside the loop.

Also notice that `x-for` is declared on a `<template>` element and not directly on the `<li>`. This is a requirement of using `x-for`. It allows Alpine to leverage the existing behavior of `<template>` tags in the browser to its advantage.

Now any element inside the `<template>` tag will be repeated for every item inside `filteredItems` and all expressions evaluated inside the loop will have direct access to the iteration variable (`item` in this case).

[→ Read more about `x-for`](https://alpinejs.dev/directives/for)

## [Recap](https://alpinejs.dev/start-here#recap)

If you've made it this far, you've been exposed to the following directives in Alpine:

- x-data
- x-on
- x-text
- x-show
- x-model
- x-for

That's a great start, however, there are many more directives to sink your teeth into. The best way to absorb Alpine is to read through this documentation. No need to comb over every word, but if you at least glance through every page you will be MUCH more effective when using Alpine.


# Start Here

Create a blank HTML file somewhere on your computer with a name like: `i-love-alpine.html`

Using a text editor, fill the file with these contents:

```
<html><head>    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script></head><body>    <h1 x-data="{ message: 'I ❤️ Alpine' }" x-text="message"></h1></body></html>
```

Open your file in a web browser, if you see `I ❤️ Alpine`, you're ready to rumble!

Now that you're all set up to play around, let's look at three practical examples as a foundation for teaching you the basics of Alpine. By the end of this exercise, you should be more than equipped to start building stuff on your own. Let's goooooo.

- [Building a counter](https://alpinejs.dev/start-here#building-a-counter)
- [Building a dropdown](https://alpinejs.dev/start-here#building-a-dropdown)
- [Building a search Input](https://alpinejs.dev/start-here#building-a-search-input)

## [Building a counter](https://alpinejs.dev/start-here#building-a-counter)

Let's start with a simple "counter" component to demonstrate the basics of state and event listening in Alpine, two core features.

Insert the following into the `<body>` tag:

```
<div x-data="{ count: 0 }">    <button x-on:click="count++">Increment</button>     <span x-text="count"></span></div>
```

Increment 0

Now, you can see with 3 bits of Alpine sprinkled into this HTML, we've created an interactive "counter" component.

Let's walk through what's happening briefly:

### [Declaring data](https://alpinejs.dev/start-here#declaring-data)

```
<div x-data="{ count: 0 }">
```

Everything in Alpine starts with an `x-data` directive. Inside of `x-data`, in plain JavaScript, you declare an object of data that Alpine will track.

Every property inside this object will be made available to other directives inside this HTML element. In addition, when one of these properties changes, everything that relies on it will change as well.

> `x-data` is required on a parent element for most Alpine directives to work.

[→ Read more about `x-data`](https://alpinejs.dev/directives/data)

Let's look at `x-on` and see how it can access and modify the `count` property from above:

### [Listening for events](https://alpinejs.dev/start-here#listening-for-events)

```
<button x-on:click="count++">Increment</button>
```

`x-on` is a directive you can use to listen for any event on an element. We're listening for a `click` event in this case, so ours looks like `x-on:click`.

You can listen for other events as you'd imagine. For example, listening for a `mouseenter` event would look like this: `x-on:mouseenter`.

When a `click` event happens, Alpine will call the associated JavaScript expression, `count++` in our case. As you can see, we have direct access to data declared in the `x-data` expression.

> You will often see `@` instead of `x-on:`. This is a shorter, friendlier syntax that many prefer. From now on, this documentation will likely use `@` instead of `x-on:`.

[→ Read more about `x-on`](https://alpinejs.dev/directives/on)

### [Reacting to changes](https://alpinejs.dev/start-here#reacting-to-changes)

```
<span x-text="count"></span>
```

`x-text` is an Alpine directive you can use to set the text content of an element to the result of a JavaScript expression.

In this case, we're telling Alpine to always make sure that the contents of this `span` tag reflect the value of the `count` property.

In case it's not clear, `x-text`, like most directives accepts a plain JavaScript expression as an argument. So for example, you could instead set its contents to: `x-text="count * 2"` and the text content of the `span` will now always be 2 times the value of `count`.

[→ Read more about `x-text`](https://alpinejs.dev/directives/text)

## [Building a dropdown](https://alpinejs.dev/start-here#building-a-dropdown)

Now that we've seen some basic functionality, let's keep going and look at an important directive in Alpine: `x-show`, by building a contrived "dropdown" component.

Insert the following code into the `<body>` tag:

```
<div x-data="{ open: false }">    <button @click="open = ! open">Toggle</button>     <div x-show="open" @click.outside="open = false">Contents...</div></div>
```

Toggle

If you load this component, you should see that the "Contents..." are hidden by default. You can toggle showing them on the page by clicking the "Toggle" button.

The `x-data` and `x-on` directives should be familiar to you from the previous example, so we'll skip those explanations.

### [Toggling elements](https://alpinejs.dev/start-here#toggling-elements)

```
<div x-show="open" ...>Contents...</div>
```

`x-show` is an extremely powerful directive in Alpine that can be used to show and hide a block of HTML on a page based on the result of a JavaScript expression, in our case: `open`.

[→ Read more about `x-show`](https://alpinejs.dev/directives/show)

### [Listening for a click outside](https://alpinejs.dev/start-here#listening-for-a-click-outside)

```
<div ... @click.outside="open = false">Contents...</div>
```

You'll notice something new in this example: `.outside`. Many directives in Alpine accept "modifiers" that are chained onto the end of the directive and are separated by periods.

In this case, `.outside` tells Alpine to instead of listening for a click INSIDE the `<div>`, to listen for the click only if it happens OUTSIDE the `<div>`.

This is a convenience helper built into Alpine because this is a common need and implementing it by hand is annoying and complex.

[→ Read more about `x-on` modifiers](https://alpinejs.dev/directives/on#modifiers)

## [Building a search input](https://alpinejs.dev/start-here#building-a-search-input)

Let's now build a more complex component and introduce a handful of other directives and patterns.

Insert the following code into the `<body>` tag:

```
<div    x-data="{        search: '',         items: ['foo', 'bar', 'baz'],         get filteredItems() {            return this.items.filter(                i => i.startsWith(this.search)            )        }    }">    <input x-model="search" placeholder="Search...">     <ul>        <template x-for="item in filteredItems" :key="item">            <li x-text="item"></li>        </template>    </ul></div>
```

- foo
- bar
- baz

By default, all of the "items" (foo, bar, and baz) will be shown on the page, but you can filter them by typing into the text input. As you type, the list of items will change to reflect what you're searching for.

Now there's quite a bit happening here, so let's go through this snippet piece by piece.

### [Multi line formatting](https://alpinejs.dev/start-here#multi-line-formatting)

The first thing I'd like to point out is that `x-data` now has a lot more going on in it than before. To make it easier to write and read, we've split it up into multiple lines in our HTML. This is completely optional and we'll talk more in a bit about how to avoid this problem altogether, but for now, we'll keep all of this JavaScript directly in the HTML.

### [Binding to inputs](https://alpinejs.dev/start-here#binding-to-inputs)

```
<input x-model="search" placeholder="Search...">
```

You'll notice a new directive we haven't seen yet: `x-model`.

`x-model` is used to "bind" the value of an input element with a data property: "search" from `x-data="{ search: '', ... }"` in our case.

This means that anytime the value of the input changes, the value of "search" will change to reflect that.

`x-model` is capable of much more than this simple example.

[→ Read more about `x-model`](https://alpinejs.dev/directives/model)

### [Computed properties using getters](https://alpinejs.dev/start-here#computed-properties-using-getters)

The next bit I'd like to draw your attention to is the `items` and `filteredItems` properties from the `x-data` directive.

```
{    ...    items: ['foo', 'bar', 'baz'],     get filteredItems() {        return this.items.filter(            i => i.startsWith(this.search)        )    }}
```

The `items` property should be self-explanatory. Here we are setting the value of `items` to a JavaScript array of 3 different items (foo, bar, and baz).

The interesting part of this snippet is the `filteredItems` property.

Denoted by the `get` prefix for this property, `filteredItems` is a "getter" property in this object. This means we can access `filteredItems` as if it was a normal property in our data object, but when we do, JavaScript will evaluate the provided function under the hood and return the result.

It's completely acceptable to forgo the `get` and just make this a method that you can call from the template, but some prefer the nicer syntax of the getter.

[→ Read more about JavaScript getters](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/get)

Now let's look inside the `filteredItems` getter and make sure we understand what's going on there:

```
return this.items.filter(    i => i.startsWith(this.search))
```

This is all plain JavaScript. We are first getting the array of items (foo, bar, and baz) and filtering them using the provided callback: `i => i.startsWith(this.search)`.

By passing in this callback to `filter`, we are telling JavaScript to only return the items that start with the string: `this.search`, which like we saw with `x-model` will always reflect the value of the input.

You may notice that up until now, we haven't had to use `this.` to reference properties. However, because we are working directly inside the `x-data` object, we must reference any properties using `this.[property]` instead of simply `[property]`.

Because Alpine is a "reactive" framework. Any time the value of `this.search` changes, parts of the template that use `filteredItems` will automatically be updated.

### [Looping elements](https://alpinejs.dev/start-here#looping-elements)

Now that we understand the data part of our component, let's understand what's happening in the template that allows us to loop through `filteredItems` on the page.

```
<ul>    <template x-for="item in filteredItems">        <li x-text="item"></li>    </template></ul>
```

The first thing to notice here is the `x-for` directive. `x-for` expressions take the following form: `[item] in [items]` where [items] is any array of data, and [item] is the name of the variable that will be assigned to an iteration inside the loop.

Also notice that `x-for` is declared on a `<template>` element and not directly on the `<li>`. This is a requirement of using `x-for`. It allows Alpine to leverage the existing behavior of `<template>` tags in the browser to its advantage.

Now any element inside the `<template>` tag will be repeated for every item inside `filteredItems` and all expressions evaluated inside the loop will have direct access to the iteration variable (`item` in this case).

[→ Read more about `x-for`](https://alpinejs.dev/directives/for)

## [Recap](https://alpinejs.dev/start-here#recap)

If you've made it this far, you've been exposed to the following directives in Alpine:

- x-data
- x-on
- x-text
- x-show
- x-model
- x-for

That's a great start, however, there are many more directives to sink your teeth into. The best way to absorb Alpine is to read through this documentation. No need to comb over every word, but if you at least glance through every page you will be MUCH more effective when using Alpine.


# Intersect Plugin

Alpine's Intersect plugin is a convenience wrapper for [Intersection Observer](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API) that allows you to easily react when an element enters the viewport.

This is useful for: lazy loading images and other content, triggering animations, infinite scrolling, logging "views" of content, etc.

## [Installation](https://alpinejs.dev/plugins/intersect#installation)

You can use this plugin by either including it from a `<script>` tag or installing it via NPM:

### Via CDN

You can include the CDN build of this plugin as a `<script>` tag, just make sure to include it BEFORE Alpine's core JS file.

```
<!-- Alpine Plugins --><script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/intersect@3.x.x/dist/cdn.min.js"></script> <!-- Alpine Core --><script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

### Via NPM

You can install Intersect from NPM for use inside your bundle like so:

```
npm install @alpinejs/intersect
```

Then initialize it from your bundle:

```
import Alpine from 'alpinejs'import intersect from '@alpinejs/intersect' Alpine.plugin(intersect) ...
```

## [x-intersect](https://alpinejs.dev/plugins/intersect#x-intersect)

The primary API for using this plugin is `x-intersect`. You can add `x-intersect` to any element within an Alpine component, and when that component enters the viewport (is scrolled into view), the provided expression will execute.

For example, in the following snippet, `shown` will remain `false` until the element is scrolled into view. At that point, the expression will execute and `shown` will become `true`:

```
<div x-data="{ shown: false }" x-intersect="shown = true">    <div x-show="shown" x-transition>        I'm in the viewport!    </div></div>
```

[Scroll Down 👇](https://alpinejs.dev/plugins/intersect#)

### [x-intersect:enter](https://alpinejs.dev/plugins/intersect#x-intersect-enter)

The `:enter` suffix is an alias of `x-intersect`, and works the same way:

```
<div x-intersect:enter="shown = true">...</div>
```

You may choose to use this for clarity when also using the `:leave` suffix.

### [x-intersect:leave](https://alpinejs.dev/plugins/intersect#x-intersect-leave)

Appending `:leave` runs your expression when the element leaves the viewport.

```
<div x-intersect:leave="shown = true">...</div>
```

> By default, this means the _whole element_ is not in the viewport. Use `x-intersect:leave.full` to run your expression when only _parts of the element_ are not in the viewport.

[→ Read more about the underlying `IntersectionObserver` API](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API)

## [Modifiers](https://alpinejs.dev/plugins/intersect#modifiers)

### [.once](https://alpinejs.dev/plugins/intersect#once)

Sometimes it's useful to evaluate an expression only the first time an element enters the viewport and not subsequent times. For example when triggering "enter" animations. In these cases, you can add the `.once` modifier to `x-intersect` to achieve this.

```
<div x-intersect.once="shown = true">...</div>
```

### [.half](https://alpinejs.dev/plugins/intersect#half)

Evaluates the expression once the intersection threshold exceeds `0.5`.

Useful for elements where it's important to show at least part of the element.

```
<div x-intersect.half="shown = true">...</div> // when `0.5` of the element is in the viewport
```

### [.full](https://alpinejs.dev/plugins/intersect#full)

Evaluates the expression once the intersection threshold exceeds `0.99`.

Useful for elements where it's important to show the whole element.

```
<div x-intersect.full="shown = true">...</div> // when `0.99` of the element is in the viewport
```

### [.threshold](https://alpinejs.dev/plugins/intersect#threshold)

Allows you to control the `threshold` property of the underlying `IntersectionObserver`:

This value should be in the range of "0-100". A value of "0" means: trigger an "intersection" if ANY part of the element enters the viewport (the default behavior). While a value of "100" means: don't trigger an "intersection" unless the entire element has entered the viewport.

Any value in between is a percentage of those two extremes.

For example if you want to trigger an intersection after half of the element has entered the page, you can use `.threshold.50`:

```
<div x-intersect.threshold.50="shown = true">...</div> // when 50% of the element is in the viewport
```

If you wanted to trigger only when 5% of the element has entered the viewport, you could use: `.threshold.05`, and so on and so forth.

### [.margin](https://alpinejs.dev/plugins/intersect#margin)

Allows you to control the `rootMargin` property of the underlying `IntersectionObserver`. This effectively tweaks the size of the viewport boundary. Positive values expand the boundary beyond the viewport, and negative values shrink it inward. The values work like CSS margin: one value for all sides; two values for top/bottom, left/right; or four values for top, right, bottom, left. You can use `px` and `%` values, or use a bare number to get a pixel value.

```
<div x-intersect.margin.200px="loaded = true">...</div> // Load when the element is within 200px of the viewport
```

```
<div x-intersect:leave.margin.10%.25px.25.25px="loaded = false">...</div> // Unload when the element gets within 10% of the top of the viewport, or within 25px of the other three edges
```

```
<div x-intersect.margin.-100px="visible = true">...</div> // Mark as visible when element is more tha
```

# Resize Plugin

Alpine's Resize plugin is a convenience wrapper for the [Resize Observer](https://developer.mozilla.org/en-US/docs/Web/API/Resize_Observer_API) that allows you to easily react when an element changes size.

This is useful for: custom size-based animations, intelligent sticky positioning, conditionally adding attributes based on the element's size, etc.

## [Installation](https://alpinejs.dev/plugins/resize#installation)

You can use this plugin by either including it from a `<script>` tag or installing it via NPM:

### Via CDN

You can include the CDN build of this plugin as a `<script>` tag, just make sure to include it BEFORE Alpine's core JS file.

```
<!-- Alpine Plugins --><script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/resize@3.x.x/dist/cdn.min.js"></script> <!-- Alpine Core --><script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

### Via NPM

You can install Resize from NPM for use inside your bundle like so:

```
npm install @alpinejs/resize
```

Then initialize it from your bundle:

```
import Alpine from 'alpinejs'import resize from '@alpinejs/resize' Alpine.plugin(resize) ...
```

## [x-resize](https://alpinejs.dev/plugins/resize#x-resize)

The primary API for using this plugin is `x-resize`. You can add `x-resize` to any element within an Alpine component, and when that element is resized for any reason, the provided expression will execute with two magic properties: `$width` and `$height`.

For example, here's a simple example of using `x-resize` to display the width and height of an element as it changes size.

```
<div    x-data="{ width: 0, height: 0 }"    x-resize="width = $width; height = $height">    <p x-text="'Width: ' + width + 'px'"></p>    <p x-text="'Height: ' + height + 'px'"></p></div>
```

_Resize your browser window to see the width and height values change._  
  

Width: 686px

Height: 104px

## [Modifiers](https://alpinejs.dev/plugins/resize#modifiers)

### [.document](https://alpinejs.dev/plugins/resize#document)

It's often useful to observe the entire document's size, rather than a specific element. To do this, you can add the `.document` modifier to `x-resize`:

```
<div x-resize.document="...">
```

_Resize your browser window to see the document width and height values change._  
  

Width: 1665px

Height: 2467.5px


# Persist Plugin

Alpine's Persist plugin allows you to persist Alpine state across page loads.

This is useful for persisting search filters, active tabs, and other features where users will be frustrated if their configuration is reset after refreshing or leaving and revisiting a page.

## [Installation](https://alpinejs.dev/plugins/persist#installation)

You can use this plugin by either including it from a `<script>` tag or installing it via NPM:

### Via CDN

You can include the CDN build of this plugin as a `<script>` tag, just make sure to include it BEFORE Alpine's core JS file.

```
<!-- Alpine Plugins --><script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/persist@3.x.x/dist/cdn.min.js"></script> <!-- Alpine Core --><script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

### Via NPM

You can install Persist from NPM for use inside your bundle like so:

```
npm install @alpinejs/persist
```

Then initialize it from your bundle:

```
import Alpine from 'alpinejs'import persist from '@alpinejs/persist' Alpine.plugin(persist) ...
```

## [$persist](https://alpinejs.dev/plugins/persist#magic-persist)

The primary API for using this plugin is the magic `$persist` method.

You can wrap any value inside `x-data` with `$persist` like below to persist its value across page loads:

```
<div x-data="{ count: $persist(0) }">    <button x-on:click="count++">Increment</button>     <span x-text="count"></span></div>
```

Increment 0

In the above example, because we wrapped `0` in `$persist()`, Alpine will now intercept changes made to `count` and persist them across page loads.

You can try this for yourself by incrementing the "count" in the above example, then refreshing this page and observing that the "count" maintains its state and isn't reset to "0".

## [How does it work?](https://alpinejs.dev/plugins/persist#how-it-works)

If a value is wrapped in `$persist`, on initialization Alpine will register its own watcher for that value. Now everytime that value changes for any reason, Alpine will store the new value in [localStorage](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage).

Now when a page is reloaded, Alpine will check localStorage (using the name of the property as the key) for a value. If it finds one, it will set the property value from localStorage immediately.

You can observe this behavior by opening your browser devtool's localStorage viewer:

[![Chrome devtools showing the localStorage view with count set to 0](https://alpinejs.dev/img/persist_devtools.png)](https://developer.chrome.com/docs/devtools/storage/localstorage/)

You'll observe that by simply visiting this page, Alpine already set the value of "count" in localStorage. You'll also notice it prefixes the property name "count" with "_x_" as a way of namespacing these values so Alpine doesn't conflict with other tools using localStorage.

Now change the "count" in the following example and observe the changes made by Alpine to localStorage:

```
<div x-data="{ count: $persist(0) }">    <button x-on:click="count++">Increment</button>     <span x-text="count"></span></div>
```

Increment 0

> `$persist` works with primitive values as well as with arrays and objects. However, it is worth noting that localStorage must be cleared when the type of the variable changes.  
> Given the previous example, if we change count to a value of `$persist({ value: 0 })`, then localStorage must be cleared or the variable 'count' renamed.

## [Setting a custom key](https://alpinejs.dev/plugins/persist#custom-key)

By default, Alpine uses the property key that `$persist(...)` is being assigned to ("count" in the above examples).

Consider the scenario where you have multiple Alpine components across pages or even on the same page that all use "count" as the property key.

Alpine will have no way of differentiating between these components.

In these cases, you can set your own custom key for any persisted value using the `.as` modifier like so:

```
<div x-data="{ count: $persist(0).as('other-count') }">    <button x-on:click="count++">Increment</button>     <span x-text="count"></span></div>
```

Now Alpine will store and retrieve the above "count" value using the key "other-count".

Here's a view of Chrome Devtools to see for yourself:

![Chrome devtools showing the localStorage view with count set to 0](https://alpinejs.dev/img/persist_custom_key_devtools.png)

## [Using a custom storage](https://alpinejs.dev/plugins/persist#custom-storage)

By default, data is saved to localStorage, it does not have an expiration time and it's kept even when the page is closed.

Consider the scenario where you want to clear the data once the user close the tab. In this case you can persist data to sessionStorage using the `.using` modifier like so:

```
<div x-data="{ count: $persist(0).using(sessionStorage) }">    <button x-on:click="count++">Increment</button>     <span x-text="count"></span></div>
```

You can also define your custom storage object exposing a getItem function and a setItem function. For example, you can decide to use a session cookie as storage doing so:

```
<script>    window.cookieStorage = {        getItem(key) {            let cookies = document.cookie.split(";");            for (let i = 0; i < cookies.length; i++) {                let cookie = cookies[i].split("=");                if (key == cookie[0].trim()) {                    return decodeURIComponent(cookie[1]);                }            }            return null;        },        setItem(key, value) {            document.cookie = key+' = '+encodeURIComponent(value)        }    }</script> <div x-data="{ count: $persist(0).using(cookieStorage) }">    <button x-on:click="count++">Increment</button>     <span x-text="count"></span></div>
```

## [Using $persist with Alpine.data](https://alpinejs.dev/plugins/persist#using-persist-with-alpine-data)

If you want to use `$persist` with `Alpine.data`, you need to use a standard function instead of an arrow function so Alpine can bind a custom `this` context when it initially evaluates the component scope.

```
Alpine.data('dropdown', function () {    return {        open: this.$persist(false)    }})
```

## [Using the Alpine.$persist global](https://alpinejs.dev/plugins/persist#using-alpine-persist-global)

`Alpine.$persist` is exposed globally so it can be used outside of `x-data` contexts. This is useful to persist data from other sources such as `Alpine.store`.

```
Alpine.store('darkMode', {    on: Alpine.$persist(true).as('darkMode_on')});
```

> Notice: This Plugin was previously called "Trap". Trap's functionality has been absorbed into this plugin along with additional functionality. You can swap Trap for Focus without any breaking changes.

# Focus Plugin

Alpine's Focus plugin allows you to manage focus on a page.

> This plugin internally makes heavy use of the open source tool: [Tabbable](https://github.com/focus-trap/tabbable). Big thanks to that team for providing a much needed solution to this problem.

## [Installation](https://alpinejs.dev/plugins/focus#installation)

You can use this plugin by either including it from a `<script>` tag or installing it via NPM:

### Via CDN

You can include the CDN build of this plugin as a `<script>` tag, just make sure to include it BEFORE Alpine's core JS file.

```
<!-- Alpine Plugins --><script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/focus@3.x.x/dist/cdn.min.js"></script> <!-- Alpine Core --><script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

### Via NPM

You can install Focus from NPM for use inside your bundle like so:

```
npm install @alpinejs/focus
```

Then initialize it from your bundle:

```
import Alpine from 'alpinejs'import focus from '@alpinejs/focus' Alpine.plugin(focus) ...
```

## [x-trap](https://alpinejs.dev/plugins/focus#x-trap)

Focus offers a dedicated API for trapping focus within an element: the `x-trap` directive.

`x-trap` accepts a JS expression. If the result of that expression is true, then the focus will be trapped inside that element until the expression becomes false, then at that point, focus will be returned to where it was previously.

For example:

```
<div x-data="{ open: false }">    <button @click="open = true">Open Dialog</button>     <span x-show="open" x-trap="open">        <p>...</p>         <input type="text" placeholder="Some input...">         <input type="text" placeholder="Some other input...">         <button @click="open = false">Close Dialog</button>    </span></div>
```

Open Dialog

### [Nesting dialogs](https://alpinejs.dev/plugins/focus#nesting)

Sometimes you may want to nest one dialog inside another. `x-trap` makes this trivial and handles it automatically.

`x-trap` keeps track of newly "trapped" elements and stores the last actively focused element. Once the element is "untrapped" then the focus will be returned to where it was originally.

This mechanism is recursive, so you can trap focus within an already trapped element infinite times, then "untrap" each element successively.

Here is nesting in action:

```
<div x-data="{ open: false }">    <button @click="open = true">Open Dialog</button>     <span x-show="open" x-trap="open">         ...         <div x-data="{ open: false }">            <button @click="open = true">Open Nested Dialog</button>             <span x-show="open" x-trap="open">                 ...                 <button @click="open = false">Close Nested Dialog</button>            </span>        </div>         <button @click="open = false">Close Dialog</button>    </span></div>
```

Open Dialog

### [Modifiers](https://alpinejs.dev/plugins/focus#modifiers)

#### [.inert](https://alpinejs.dev/plugins/focus#inert)

When building things like dialogs/modals, it's recommended to hide all the other elements on the page from screen readers when trapping focus.

By adding `.inert` to `x-trap`, when focus is trapped, all other elements on the page will receive `aria-hidden="true"` attributes, and when focus trapping is disabled, those attributes will also be removed.

```
<!-- When `open` is `false`: --><body x-data="{ open: false }">    <div x-trap.inert="open" ...>        ...    </div>     <div>        ...    </div></body> <!-- When `open` is `true`: --><body x-data="{ open: true }">    <div x-trap.inert="open" ...>        ...    </div>     <div aria-hidden="true">        ...    </div></body>
```

#### [.noscroll](https://alpinejs.dev/plugins/focus#noscroll)

When building dialogs/modals with Alpine, it's recommended that you disable scrolling for the surrounding content when the dialog is open.

`x-trap` allows you to do this automatically with the `.noscroll` modifiers.

By adding `.noscroll`, Alpine will remove the scrollbar from the page and block users from scrolling down the page while a dialog is open.

For example:

```
<div x-data="{ open: false }">    <button @click="open = true">Open Dialog</button>     <div x-show="open" x-trap.noscroll="open">        Dialog Contents         <button @click="open = false">Close Dialog</button>    </div></div>
```

Open Dialog

#### [.noreturn](https://alpinejs.dev/plugins/focus#noreturn)

Sometimes you may not want focus to be returned to where it was previously. Consider a dropdown that's triggered upon focusing an input, returning focus to the input on close will just trigger the dropdown to open again.

`x-trap` allows you to disable this behavior with the `.noreturn` modifier.

By adding `.noreturn`, Alpine will not return focus upon x-trap evaluating to false.

For example:

```
<div x-data="{ open: false }" x-trap.noreturn="open">    <input type="search" placeholder="search for something" />     <div x-show="open">        Search results         <button @click="open = false">Close</button>    </div></div>
```

#### [.noautofocus](https://alpinejs.dev/plugins/focus#noautofocus)

By default, when `x-trap` traps focus within an element, it focuses the first focussable element within that element. This is a sensible default, however there are times where you may want to disable this behavior and not automatically focus any elements when `x-trap` engages.

By adding `.noautofocus`, Alpine will not automatically focus any elements when trapping focus.

## [$focus](https://alpinejs.dev/plugins/focus#focus-magic)

This plugin offers many smaller utilities for managing focus within a page. These utilities are exposed via the `$focus` magic.

|Property|Description|
|---|---|
|`focus(el)`|Focus the passed element (handling annoyances internally: using nextTick, etc.)|
|`focusable(el)`|Detect whether or not an element is focusable|
|`focusables()`|Get all "focusable" elements within the current element|
|`focused()`|Get the currently focused element on the page|
|`lastFocused()`|Get the last focused element on the page|
|`within(el)`|Specify an element to scope the `$focus` magic to (the current element by default)|
|`first()`|Focus the first focusable element|
|`last()`|Focus the last focusable element|
|`next()`|Focus the next focusable element|
|`previous()`|Focus the previous focusable element|
|`noscroll()`|Prevent scrolling to the element about to be focused|
|`wrap()`|When retrieving "next" or "previous" use "wrap around" (ex. returning the first element if getting the "next" element of the last element)|
|`getFirst()`|Retrieve the first focusable element|
|`getLast()`|Retrieve the last focusable element|
|`getNext()`|Retrieve the next focusable element|
|`getPrevious()`|Retrieve the previous focusable element|

Let's walk through a few examples of these utilities in use. The example below allows the user to control focus within the group of buttons using the arrow keys. You can test this by clicking on a button, then using the arrow keys to move focus around:

```
<div    @keydown.right="$focus.next()"    @keydown.left="$focus.previous()">    <button>First</button>    <button>Second</button>    <button>Third</button></div>
```

First Second Third

(Click a button, then use the arrow keys to move left and right)

Notice how if the last button is focused, pressing "right arrow" won't do anything. Let's add the `.wrap()` method so that focus "wraps around":

```
<div    @keydown.right="$focus.wrap().next()"    @keydown.left="$focus.wrap().previous()">    <button>First</button>    <button>Second</button>    <button>Third</button></div>
```

First Second Third

(Click a button, then use the arrow keys to move left and right)

Now, let's add two buttons, one to focus the first element in the button group, and another focus the last element:

```
<button @click="$focus.within($refs.buttons).first()">Focus "First"</button><button @click="$focus.within($refs.buttons).last()">Focus "Last"</button> <div    x-ref="buttons"    @keydown.right="$focus.wrap().next()"    @keydown.left="$focus.wrap().previous()">    <button>First</button>    <button>Second</button>    <button>Third</button></div>
```

Focus "First" Focus "Last"

---

First Second Third

Notice that we needed to add a `.within()` method for each button so that `$focus` knows to scope itself to a different element (the `div` wrapping the buttons).


# Collapse Plugin

Alpine's Collapse plugin allows you to expand and collapse elements using smooth animations.

Because this behavior and implementation differs from Alpine's standard transition system, this functionality was made into a dedicated plugin.

## [Installation](https://alpinejs.dev/plugins/collapse#installation)

You can use this plugin by either including it from a `<script>` tag or installing it via NPM:

### Via CDN

You can include the CDN build of this plugin as a `<script>` tag, just make sure to include it BEFORE Alpine's core JS file.

```
<!-- Alpine Plugins --><script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/collapse@3.x.x/dist/cdn.min.js"></script> <!-- Alpine Core --><script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

### Via NPM

You can install Collapse from NPM for use inside your bundle like so:

```
npm install @alpinejs/collapse
```

Then initialize it from your bundle:

```
import Alpine from 'alpinejs'import collapse from '@alpinejs/collapse' Alpine.plugin(collapse) ...
```

## [x-collapse](https://alpinejs.dev/plugins/collapse#x-collapse)

The primary API for using this plugin is the `x-collapse` directive.

`x-collapse` can only exist on an element that already has an `x-show` directive. When added to an `x-show` element, `x-collapse` will smoothly "collapse" and "expand" the element when it's visibility is toggled by animating its height property.

For example:

```
<div x-data="{ expanded: false }">    <button @click="expanded = ! expanded">Toggle Content</button>     <p x-show="expanded" x-collapse>        ...    </p></div>
```

Toggle Content

## [Modifiers](https://alpinejs.dev/plugins/collapse#modifiers)

### [.duration](https://alpinejs.dev/plugins/collapse#dot-duration)

You can customize the duration of the collapse/expand transition by appending the `.duration` modifier like so:

```
<div x-data="{ expanded: false }">    <button @click="expanded = ! expanded">Toggle Content</button>     <p x-show="expanded" x-collapse.duration.1000ms>        ...    </p></div>
```

Toggle Content

### [.min](https://alpinejs.dev/plugins/collapse#dot-min)

By default, `x-collapse`'s "collapsed" state sets the height of the element to `0px` and also sets `display: none;`.

Sometimes, it's helpful to "cut-off" an element rather than fully hide it. By using the `.min` modifier, you can set a minimum height for `x-collapse`'s "collapsed" state. For example:

```
<div x-data="{ expanded: false }">    <button @click="expanded = ! expanded">Toggle Content</button>     <p x-show="expanded" x-collapse.min.50px>        ...    </p></div>
```

Toggle Content

Reprehenderit eu excepteur ullamco esse cillum reprehenderit exercitation labore non. Dolore dolore ea dolore veniam sint in sint ex Lorem ipsum. Sint laborum deserunt deserunt amet voluptate cillum deserunt. Amet nisi pariatur sit ut id. Ipsum est minim est commodo id dolor sint id quis sint Lorem.

[← Focus](https://alpinejs.dev/plugins/focus)


# Anchor Plugin

Alpine's Anchor plugin allows you to easily anchor an element's positioning to another element on the page.

This functionality is useful when creating dropdown menus, popovers, dialogs, and tooltips with Alpine.

The "anchoring" functionality used in this plugin is provided by the [Floating UI](https://floating-ui.com/) project.

## [Installation](https://alpinejs.dev/plugins/anchor#installation)

You can use this plugin by either including it from a `<script>` tag or installing it via NPM:

### Via CDN

You can include the CDN build of this plugin as a `<script>` tag, just make sure to include it BEFORE Alpine's core JS file.

```
<!-- Alpine Plugins --><script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/anchor@3.x.x/dist/cdn.min.js"></script> <!-- Alpine Core --><script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

### Via NPM

You can install Anchor from NPM for use inside your bundle like so:

```
npm install @alpinejs/anchor
```

Then initialize it from your bundle:

```
import Alpine from 'alpinejs'import anchor from '@alpinejs/anchor' Alpine.plugin(anchor) ...
```

## [x-anchor](https://alpinejs.dev/plugins/anchor#x-anchor)

The primary API for using this plugin is the `x-anchor` directive.

To use this plugin, add the `x-anchor` directive to any element and pass it a reference to the element you want to anchor it's position to (often a button on the page).

By default, `x-anchor` will set the element's CSS to `position: absolute` and the appropriate `top` and `left` values. If the anchored element is normally displayed below the reference element but doesn't have room on the page, it's styling will be adjusted to render above the element.

For example, here's a simple dropdown anchored to the button that toggles it:

```
<div x-data="{ open: false }">    <button x-ref="button" @click="open = ! open">Toggle</button>     <div x-show="open" x-anchor="$refs.button">        Dropdown content    </div></div>
```

Toggle

## [Positioning](https://alpinejs.dev/plugins/anchor#positioning)

`x-anchor` allows you to customize the positioning of the anchored element using the following modifiers:

- Bottom: `.bottom`, `.bottom-start`, `.bottom-end`
- Top: `.top`, `.top-start`, `.top-end`
- Left: `.left`, `.left-start`, `.left-end`
- Right: `.right`, `.right-start`, `.right-end`

Here is an example of using `.bottom-start` to position a dropdown below and to the right of the reference element:

```
<div x-data="{ open: false }">    <button x-ref="button" @click="open = ! open">Toggle</button>     <div x-show="open" x-anchor.bottom-start="$refs.button">        Dropdown content    </div></div>
```

Toggle

## [Offset](https://alpinejs.dev/plugins/anchor#offset)

You can add an offset to your anchored element using the `.offset.[px value]` modifier like so:

```
<div x-data="{ open: false }">    <button x-ref="button" @click="open = ! open">Toggle</button>     <div x-show="open" x-anchor.offset.10="$refs.button">        Dropdown content    </div></div>
```

Toggle

## [Manual styling](https://alpinejs.dev/plugins/anchor#manual-styling)

By default, `x-anchor` applies the positioning styles to your element under the hood. If you'd prefer full control over styling, you can pass the `.no-style` modifer and use the `$anchor` magic to access the values inside another Alpine expression.

Below is an example of bypassing `x-anchor`'s internal styling and instead applying the styles yourself using `x-bind:style`:

```
<div x-data="{ open: false }">    <button x-ref="button" @click="open = ! open">Toggle</button>     <div        x-show="open"        x-anchor.no-style="$refs.button"        x-bind:style="{ position: 'absolute', top: $anchor.y+'px', left: $anchor.x+'px' }"    >        Dropdown content    </div></div>
```

Toggle

## [Anchor to an ID](https://alpinejs.dev/plugins/anchor#from-id)

The examples thus far have all been anchoring to other elements using Alpine refs.

Because `x-anchor` accepts a reference to any DOM element, you can use utilities like `document.getElementById()` to anchor to an element by its `id` attribute:

```
<div x-data="{ open: false }">    <button id="trigger" @click="open = ! open">Toggle</button>     <div x-show="open" x-anchor="document.getElementById('trigger')">        Dropdown content    </div></div>
```

Toggle

# Morph Plugin

Alpine's Morph plugin allows you to "morph" an element on the page into the provided HTML template, all while preserving any browser or Alpine state within the "morphed" element.

This is useful for updating HTML from a server request without losing Alpine's on-page state. A utility like this is at the core of full-stack frameworks like [Laravel Livewire](https://laravel-livewire.com/) and [Phoenix LiveView](https://dockyard.com/blog/2018/12/12/phoenix-liveview-interactive-real-time-apps-no-need-to-write-javascript).

The best way to understand its purpose is with the following interactive visualization. Give it a try!

![](https://alpinejs.dev/img/morphs/morph1.png)

Previous

Next

## [Installation](https://alpinejs.dev/plugins/morph#installation)

You can use this plugin by either including it from a `<script>` tag or installing it via NPM:

### Via CDN

You can include the CDN build of this plugin as a `<script>` tag, just make sure to include it BEFORE Alpine's core JS file.

```
<!-- Alpine Plugins --><script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/morph@3.x.x/dist/cdn.min.js"></script> <!-- Alpine Core --><script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

### Via NPM

You can install Morph from NPM for use inside your bundle like so:

```
npm install @alpinejs/morph
```

Then initialize it from your bundle:

```
import Alpine from 'alpinejs'import morph from '@alpinejs/morph' window.Alpine = AlpineAlpine.plugin(morph) ...
```

## [Alpine.morph()](https://alpinejs.dev/plugins/morph#alpine-morph)

The `Alpine.morph(el, newHtml)` allows you to imperatively morph a dom node based on passed in HTML. It accepts the following parameters:

|Parameter|Description|
|---|---|
|`el`|A DOM element on the page.|
|`newHtml`|A string of HTML to use as the template to morph the dom element into.|
|`options` (optional)|An options object used mainly for [injecting lifecycle hooks](https://alpinejs.dev/plugins/morph#lifecycle-hooks).|

Here's an example of using `Alpine.morph()` to update an Alpine component with new HTML: (In real apps, this new HTML would likely be coming from the server)

```
<div x-data="{ message: 'Change me, then press the button!' }">    <input type="text" x-model="message">    <span x-text="message"></span></div> <button>Run Morph</button> <script>    document.querySelector('button').addEventListener('click', () => {        let el = document.querySelector('div')         Alpine.morph(el, `            <div x-data="{ message: 'Change me, then press the button!' }">                <h2>See how new elements have been added</h2>                 <input type="text" x-model="message">                <span x-text="message"></span>                 <h2>but the state of this component hasn't changed? Magical.</h2>            </div>        `)    })</script>
```

 Change me, then press the button!

Run Morph

### [Lifecycle Hooks](https://alpinejs.dev/plugins/morph#lifecycle-hooks)

The "Morph" plugin works by comparing two DOM trees, the live element, and the passed in HTML.

Morph walks both trees simultaneously and compares each node and its children. If it finds differences, it "patches" (changes) the current DOM tree to match the passed in HTML's tree.

While the default algorithm is very capable, there are cases where you may want to hook into its lifecycle and observe or change its behavior as it's happening.

Before we jump into the available Lifecycle hooks themselves, let's first list out all the potential parameters they receive and explain what each one is:

|Parameter|Description|
|---|---|
|`el`|This is always the actual, current, DOM element on the page that will be "patched" (changed by Morph).|
|`toEl`|This is a "template element". It's a temporary element representing what the live `el` will be patched to. It will never actually live on the page and should only be used for reference purposes.|
|`childrenOnly()`|This is a function that can be called inside the hook to tell Morph to skip the current element and only "patch" its children.|
|`skip()`|A function that when called within the hook will "skip" comparing/patching itself and the children of the current element.|

Here are the available lifecycle hooks (passed in as the third parameter to `Alpine.morph(..., options)`):

|Option|Description|
|---|---|
|`updating(el, toEl, childrenOnly, skip)`|Called before patching the `el` with the comparison `toEl`.|
|`updated(el, toEl)`|Called after Morph has patched `el`.|
|`removing(el, skip)`|Called before Morph removes an element from the live DOM.|
|`removed(el)`|Called after Morph has removed an element from the live DOM.|
|`adding(el, skip)`|Called before adding a new element.|
|`added(el)`|Called after adding a new element to the live DOM tree.|
|`key(el)`|A re-usable function to determine how Morph "keys" elements in the tree before comparing/patching. [More on that here](https://alpinejs.dev/plugins/morph#keys)|
|`lookahead`|A boolean value telling Morph to enable an extra feature in its algorithm that "looks ahead" to make sure a DOM element that's about to be removed should instead just be "moved" to a later sibling.|

Here is code of all these lifecycle hooks for a more concrete reference:

```
Alpine.morph(el, newHtml, {    updating(el, toEl, childrenOnly, skip) {        //    },     updated(el, toEl) {        //    },     removing(el, skip) {        //    },     removed(el) {        //    },     adding(el, skip) {        //    },     added(el) {        //    },     key(el) {        // By default Alpine uses the `key=""` HTML attribute.        return el.id    },     lookahead: true, // Default: false})
```

### [Keys](https://alpinejs.dev/plugins/morph#keys)

Dom-diffing utilities like Morph try their best to accurately "morph" the original DOM into the new HTML. However, there are cases where it's impossible to determine if an element should be just changed, or replaced completely.

Because of this limitation, Morph has a "key" system that allows developers to "force" preserving certain elements rather than replacing them.

The most common use-case for them is a list of siblings within a loop. Below is an example of why keys are necessary sometimes:

```
<!-- "Live" Dom on the page: --><ul>    <li>Mark</li>    <li>Tom</li>    <li>Travis</li></ul> <!-- New HTML to "morph to": --><ul>    <li>Travis</li>    <li>Mark</li>    <li>Tom</li></ul>
```

Given the above situation, Morph has no way to know that the "Travis" node has been moved in the DOM tree. It just thinks that "Mark" has been changed to "Travis" and "Travis" changed to "Tom".

This is not what we actually want, we want Morph to preserve the original elements and instead of changing them, MOVE them within the `<ul>`.

By adding keys to each node, we can accomplish this like so:

```
<!-- "Live" Dom on the page: --><ul>    <li key="1">Mark</li>    <li key="2">Tom</li>    <li key="3">Travis</li></ul> <!-- New HTML to "morph to": --><ul>    <li key="3">Travis</li>    <li key="1">Mark</li>    <li key="2">Tom</li></ul>
```

Now that there are "keys" on the `<li>`s, Morph will match them in both trees and move them accordingly.

You can configure what Morph considers a "key" with the `key:` configuration option. [More on that here](https://alpinejs.dev/plugins/morph#lifecycle-hooks)

## [Alpine.morphBetween()](https://alpinejs.dev/plugins/morph#alpine-morph-between)

The `Alpine.morphBetween(startMarker, endMarker, newHtml, options)` method allows you to morph a range of DOM nodes between two marker elements based on passed in HTML. This is useful when you want to update only a specific section of the DOM without providing a single root node.

|Parameter|Description|
|---|---|
|`startMarker`|A DOM node (typically a comment node) that marks the beginning of the range to morph|
|`endMarker`|A DOM node (typically a comment node) that marks the end of the range to morph|
|`newHtml`|A string of HTML or a DOM element to replace the content between the markers|
|`options`|An object of options (same as `Alpine.morph()`)|

[← Anchor](https://alpinejs.dev/plugins/anchor)

[Sort](https://alpinejs.dev/plugins/sort)

# Sort Plugin

Alpine's Sort plugin allows you to easily re-order elements by dragging them with your mouse.

This functionality is useful for things like Kanban boards, to-do lists, sortable table columns, etc.

The drag functionality used in this plugin is provided by the [SortableJS](https://github.com/SortableJS/Sortable) project.

## [Installation](https://alpinejs.dev/plugins/sort#installation)

You can use this plugin by either including it from a `<script>` tag or installing it via NPM:

### Via CDN

You can include the CDN build of this plugin as a `<script>` tag; just make sure to include it BEFORE Alpine's core JS file.

```
<!-- Alpine Plugins --><script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/sort@3.x.x/dist/cdn.min.js"></script> <!-- Alpine Core --><script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

### Via NPM

You can install Sort from NPM for use inside your bundle like so:

```
npm install @alpinejs/sort
```

Then initialize it from your bundle:

```
import Alpine from 'alpinejs'import sort from '@alpinejs/sort' Alpine.plugin(sort) ...
```

## [Basic usage](https://alpinejs.dev/plugins/sort#basic-usage)

The primary API for using this plugin is the `x-sort` directive. By adding `x-sort` to an element, its children containing `x-sort:item` become sortable—meaning you can drag them around with your mouse, and they will change positions.

```
<ul x-sort>    <li x-sort:item>foo</li>    <li x-sort:item>bar</li>    <li x-sort:item>baz</li></ul>
```

- foo
- bar
- baz

## [Sort handlers](https://alpinejs.dev/plugins/sort#sort-handlers)

You can react to sorting changes by passing a handler function to `x-sort` and adding keys to each item using `x-sort:item`. Here is an example of a simple handler function that shows an alert dialog with the changed item's key and its new position:

```
<ul x-sort="alert($item + ' - ' + $position)">    <li x-sort:item="1">foo</li>    <li x-sort:item="2">bar</li>    <li x-sort:item="3">baz</li></ul>
```

- foo
- bar
- baz

The `x-sort` handler will be called every time the sort order of the items change. The `$item` magic will contain the key of the sorted element (derived from `x-sort:item`), and `$position` will contain the new position of the item (starting at index `0`).

You can also pass a handler function to `x-sort` and that function will receive the `item` and `position` as the first and second parameter:

```
<div x-data="{ handle: (item, position) => { ... } }">    <ul x-sort="handle">        <li x-sort:item="1">foo</li>        <li x-sort:item="2">bar</li>        <li x-sort:item="3">baz</li>    </ul></div>
```

Handler functions are often used to persist the new order of items in the database so that the sorting order of a list is preserved between page refreshes.

## [Sorting groups](https://alpinejs.dev/plugins/sort#sorting-groups)

This plugin allows you to drag items from one `x-sort` sortable list into another one by adding a matching `x-sort:group` value to both lists:

```
<div>    <ul x-sort x-sort:group="todos">        <li x-sort:item="1">foo</li>        <li x-sort:item="2">bar</li>        <li x-sort:item="3">baz</li>    </ul>     <ol x-sort x-sort:group="todos">        <li x-sort:item="4">foo</li>        <li x-sort:item="5">bar</li>        <li x-sort:item="6">baz</li>    </ol></div>
```

Because both sortable lists above use the same group name (`todos`), you can drag items from one list onto another.

> When using sort handlers like `x-sort="handle"` and dragging an item from one group to another, only the destination list's handler will be called with the key and new position.

## [Drag handles](https://alpinejs.dev/plugins/sort#drag-handles)

By default, each `x-sort:item` element is draggable by clicking and dragging anywhere within it. However, you may want to designate a smaller, more specific element as the "drag handle" so that the rest of the element can be interacted with like normal, and only the handle will respond to mouse dragging:

```
<ul x-sort>    <li x-sort:item>        <span x-sort:handle> - </span>foo    </li>     <li x-sort:item>        <span x-sort:handle> - </span>bar    </li>     <li x-sort:item>        <span x-sort:handle> - </span>baz    </li></ul>
```

- - foo
- - bar
- - baz

As you can see in the above example, the hyphen "-" is draggable, but the item text ("foo") is not.

## [Ghost elements](https://alpinejs.dev/plugins/sort#ghost-elements)

When a user drags an item, the element will follow their mouse to appear as though they are physically dragging the element.

By default, a "hole" (empty space) will be left in the original element's place during the drag.

If you would like to show a "ghost" of the original element in its place instead of an empty space, you can add the `.ghost` modifier to `x-sort`:

```
<ul x-sort.ghost>    <li x-sort:item>foo</li>    <li x-sort:item>bar</li>    <li x-sort:item>baz</li></ul>
```

- foo
- bar
- baz

### [Styling the ghost element](https://alpinejs.dev/plugins/sort#ghost-styling)

By default, the "ghost" element has a `.sortable-ghost` CSS class attached to it while the original element is being dragged.

This makes it easy to add any custom styling you would like:

```
<style>.sortable-ghost {    opacity: .5 !important;}</style> <ul x-sort.ghost>    <li x-sort:item>foo</li>    <li x-sort:item>bar</li>    <li x-sort:item>baz</li></ul>
```

- foo
- bar
- baz

## [Sorting class on body](https://alpinejs.dev/plugins/sort#sorting-class)

While an element is being dragged around, Alpine will automatically add a `.sorting` class to the `<body>` element of the page.

This is useful for styling any element on the page conditionally using only CSS.

For example you could have a warning that only displays while a user is sorting items:

```
<div id="sort-warning">    Page functionality is limited while sorting</div>
```

To show this only while sorting, you can use the `body.sorting` CSS selector:

```
#sort-warning {    display: none;} body.sorting #sort-warning {    display: block;}
```

## [CSS hover bug](https://alpinejs.dev/plugins/sort#css-hover-bug)

Currently, there is a [bug in Chrome and Safari](https://issues.chromium.org/issues/41129937) (not Firefox) that causes issues with hover styles.

Consider HTML like the following, where each item in the list is styled differently based on a hover state (here we're using Tailwind's `.hover` class to conditionally add a border):

```
<div x-sort>    <div x-sort:item class="hover:border">foo</div>    <div x-sort:item class="hover:border">bar</div>    <div x-sort:item class="hover:border">baz</div></div>
```

If you drag one of the elements in the list below you will see that the hover effect will be errantly applied to any element in the original element's place:

- foo
- bar
- baz

To fix this, you can leverage the `.sorting` class applied to the body while sorting to limit the hover effect to only be applied while `.sorting` does NOT exist on `body`.

Here is how you can do this directly inline using Tailwind arbitrary variants:

```
<div x-sort>    <div x-sort:item class="[body:not(.sorting)_&]:hover:border">foo</div>    <div x-sort:item class="[body:not(.sorting)_&]:hover:border">bar</div>    <div x-sort:item class="[body:not(.sorting)_&]:hover:border">baz</div></div>
```

Now you can see below that the hover effect is only applied to the dragging element and not the others in the list.

- foo
- bar
- baz

## [Custom configuration](https://alpinejs.dev/plugins/sort#custom-configuration)

Alpine chooses sensible defaults for configuring [SortableJS](https://github.com/SortableJS/Sortable?tab=readme-ov-file#options) under the hood. However, you can add or override any of these options yourself using `x-sort:config`:

```
<ul x-sort x-sort:config="{ animation: 0 }">    <li x-sort:item>foo</li>    <li x-sort:item>bar</li>    <li x-sort:item>baz</li></ul>
```

- foo
- bar
- baz

> Any config options passed will overwrite Alpine defaults. In this case of `animation`, this is fine, however be aware that overwriting `handle`, `group`, `filter`, `onSort`, `onStart`, or `onEnd` may break functionality.

[View the full list of SortableJS configuration options here →](https://github.com/SortableJS/Sortable?tab=readme-ov-file#options)