> &nbsp;
> 
> ### 🛑 **Please note**
> 
> *I have made a significant change to the repository, removing a large CSV file that I had initially included. This is purely to save space; everyone really doesn't need to download that massive file (and any changes to it) as part of this repo.*
> 
> *But since I have fully removed the file even from the repo history, this means that if you cloned/downloaded the repo **before May 25, 2022,** you should really re-clone it now.*
> 
> &nbsp;

# EnumChronFill
This project addresses an issue in Ex Libris Alma, typically following migration (or, I suppose, following a period of poor cataloging). It's typical for a large number of serial/continuous items to have `Descriptions` that indicate enumeration &amp; chronology info, but have empty `Enum` &amp; `Chron` fields. These items appear to display correctly in Primo, but lose the functionality that derives from proper Enum &amp; Chron information&mdash;namely, the ability to sort by volume, by year, etc.

The approach of this project is to read in the `Description` field from these records, use regular expressions to derive the enumeration & chronology info it contains, and then use that to populate the `Enum`/`Chron` fields via the Alma API.

The info contained in these Description fields is pretty stunning in its variety. This has three implications:
- It would be inordinately complex to try and devise a single regex to address all possible Desc fields. So our approach will be to iterate through a number of expressions, trying to make each as versatile as we reasonably can without stumbling over false positives.
- It will be impossible for this tool to derive enum/chron info for **every** case. Our goal here is to try and get down to edge cases. Obviously, at the point where it's more difficult to construct a proper regex than it is simply to manually fix a handful of records, we'll plan to do the latter.
- Truthfully, you'll probably want to view this script as a starting point, which hopefully will cover a large number of your records. But if you have a bit of Python/RegEx knowledge, you should be able to tweak it to address quite a few more. My edge cases may well be your low-hanging fruit, in some instances. I'm pretty good with regex, and **I'm happy to help** try to come up with search &amp; replace criteria for your specific cases. Please feel free to contact me if you think I can be of assistance.

## **Let me say up front . . .**
. . . that I'm relatively new and largely self-taught when it comes to both Git and Python<sup>†</sup>. So I probably do things in not-the-most-efficient ways pretty regularly. If you have any advice for better methods to accomplish anything here, by all means please let me know.

> <b>†</b> *Though I do want to give a shout-out to Chris Diaz's  [Library Juice Academy class on Git/Github](https://libraryjuiceacademy.com/shop/course/268-git-and-github-for-libraries/). I learned a ton, and this tool began as my final project for it.*

## **Requirements**
In an effort to simplify things and avoid a lot of unnecessary API calls, this script reads its record info from a CSV file in this same directory.

> **Please note:** I have created a public Alma Analytics report to extract the proper fields, and to filter for records which have Desc but not Enum or Chron info. From the Alma Analytics catalog, navigate to `Shared Folders > Community > Reports` and you'll find the `EnumChronFix` report. From that report, you can easily export a spreadsheet custom-made for use with this tool.

If you wish to export your own CSV file from Alma, the file should be named FullItemList.csv, and it must have at least the following columns:
- MMS_ID
- Holdings_ID
- Item_ID
- Description

It's fine if these column headings have spaces rather than underscores&mdash;the script will make that change. It's also fine to have other columns in the file&mdash;the script will simply ignore them, unless you add code to which looks at them.

For my own purposes, some of our Enum/Chron fields may vary based on material type and location within the library. So, future instances of the tool may reference these columns as well. I will probably comment out these sections, because they're likely to be quite specific to our institution.

### **Dependencies**
You'll need Python to run the script, of course. At this point, the only packages you need are `pandas` and `re`. I also highly recommend `pprint`, but you can probably disable the calls for it within the script if you'd like.

## **A note on authentication**
You're also going to need appropriate API keys for your institution. Getting that set up is beyond the scope of this introduction, but I do want to mention how I've gone about implementing the authentication.

In order to keep the API credentials private, my approach is to tackle the authentication via an external file, and then call that file from these scripts.

What I've done is to create a script called `Credentials.py` which resides in this folder on my computer. To keep it private, I've added a line in the `.gitignore` file which filters it out of any pushes to the public repository. So you'll need to create your own Credentials.py file, in this same directory.

Credentials.py is a very simple file, looking like this:

    prod_api = 'a1aa11111111111111aa1a11aaaa11a111aa'
    sand_api = 'z9zzz99zzz99z9z999zzzzz999zz9999z999'

As you can see in the scripts themselves, we import that file thus:

    import Credentials

and get the API key for use thus:

    apikey = Credentials.prod_api

I hope that makes sense.
