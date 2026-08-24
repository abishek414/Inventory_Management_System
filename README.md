# Inventory Management System

A multi-tenant inventory management web app built with Django. Any organization can sign up, set up its own roles and permissions, and track stock - what's in the building, where it is, who took it, and who still owes something back.

**Live demo:** [inventorymanagement.pythonanywhere.com] (https://inventorymanagement.pythonanywhere.com)
## For Testing purpose you can use the account information provided below:
Username: Abishek
Password: Easy12345

## Why I built this

I previously worked with the Student Engagement team at Charles Darwin University as part of my placement, where one of my responsibilities is managing the resource hub - and for tracking, me and my team ended up submitting an Excel file listing every item and its location by hand. I also worked in a Coca-Cola warehouse, where hundreds of items were spread across different locations and keeping track of what was where, and what had gone out, was a constant, very manual effort.

Both experiences left me thinking the same thing: this should be a proper system, not a spreadsheet someone has to keep updating and re-submitting. Since I already had a working knowledge of Python and Django, building it as a Django web app was the natural choice - something any organization could sign up to and use for its own inventory, not just the two places I happened to work.

## Built with AI - and built fast

The code in this repository was written by [Claude.ai](https://claude.ai) (Anthropic). I went through every file myself to understand what it does and how it works, testing each change as it came in and requesting the next one.

A project like this - multi-tenant organizations, role-based permissions, a full audit trail, bulk Excel import, email-based password recovery, a mobile-responsive UI - would typically take a solo developer a week or more to build properly. This one came together in a single day. I think that's worth saying plainly: AI is a genuinely capable engineering tool right now, and used deliberately - with a clear product vision driving it rather than the other way around - it can compress that kind of timeline enormously. That's not a shortcut to hide; it's a way of working worth being upfront about.

## Features

- **Multi-organization** - anyone can create an organization and becomes its Admin.
- **Custom roles per organization** - each organization defines its own roles (e.g. Warehouse Staff, Viewer) with fine-grained permissions: view inventory, add stock, take stock, borrow items, delete items, edit items, upload via Excel, manage users.
- **Built-in Admin role** - every organization always has one role that can't be edited, deleted, or stripped of permissions, so it can never end up with nobody able to manage it.
- **Stock tracking** - add stock, take stock (permanently consumed), or borrow stock (checked out and expected back), with every change logged.
- **Borrow/return workflow** - items marked as borrowable can be checked out and later marked returned. Only the person who borrowed an item can mark it returned.
- **Full audit trail** - every stock change, take, borrow, and return is recorded with who did it and when. Regular members see their own activity, managers and Admins see everyone's.
- **Bulk Excel import** - upload a spreadsheet to create new items or restock existing ones in one pass, with a downloadable template.
- **Location tracking** - every item has its own location, independent of every other item.
- **Low-stock warnings** - items flag themselves as low or out of stock based on a configurable reorder level.
- **Self-service password reset** - a "Forgot password" flow that emails a real reset link.
- **Mobile-responsive** - the inventory list and navigation both adapt to phone-sized screens.

## Tech stack

- **Backend:** Django 5.2, Python 3.10
- **Database:** SQLite
- **Frontend:** Django templates, Bootstrap 5, Bootstrap Icons
- **Excel import/export:** openpyxl
- **Email:** Django's SMTP backend (Gmail)
- **Hosting:** PythonAnywhere

## How it works

The project is split into three Django apps, each responsible for one part of the system:

- **accounts** - the login system. A custom `User` model, separate from any organization .
- **organizations** - the multi-tenant core. Three models drive everything:
  - `Organization` - a tenant. Every other piece of data belongs to exactly one organization, and organizations never see each other's data.
  - `Role` - a permission level defined by an organization for its own members (e.g. "Warehouse Staff", "Viewer"), with a checkbox for each permission: view inventory, add stock, take stock, borrow items, delete items, edit items, upload via Excel, manage users. Every organization also gets one built-in Admin role that always has every permission switched on and can't be edited, deleted, or stripped of access - so an organization can never end up with nobody able to manage it.
  - `Membership` - links one `User` to one `Organization` with one `Role`.
- **inventory** - the stock itself:
  - `Item` - one piece of inventory, with its own quantity, unit, location, and reorder level.
  - `StockTransaction` - an audit trail entry, one row per stock-affecting action (stock added, taken, borrowed, returned, location changed, Excel import), recording who did it and when.
  - `BorrowRecord` - one checkout of a borrowable item, open until it's marked returned.

Every view in the app checks the current user's `Role` within the organization they're currently working in before it lets them do anything - so what a member can see and act on is entirely controlled by the permissions their Role has, not hardcoded per user.

## Acknowledgements

Built with help of [Claude.ai](https://claude.ai) by Anthropic.