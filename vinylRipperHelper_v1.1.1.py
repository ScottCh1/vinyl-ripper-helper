""" -------------------------------------------------------------------------------
Vinyl Ripper helper script for Audacity users, by Scott Chilcote
This software is licensed under GPLv3
(https://www.gnu.org/licenses/gpl-3.0.en.html)

The vinylRipperHelper python program:

  - Will generate two files, one containing labels, the other containing a
  metadata tags template for a record or tape album recorded using audacity

  - Requires a web page HTML file from Discogs.com for the specific album that
  was used to create the audacity recording

  - Input parameters:
     o The length of the track gap TG in between consecutive tracks, in seconds
     (default 4 seconds - this does not have to be precise)
     o Name for the output labels and tags files (default <album>-<artist>)

  - Typical ripping workflow to use this script:
    1. Find your record album on Discogs.  Display the album page that shows the
    tracklist for the album.
    2. Save the HTML page file to a local directory
    3. Record the record album using audacity and save the project file
    4. Measure the gap between tracks TG in seconds
    5. Make a single recording that includes all record/tape sides in order
    6. Optional: If you do any preprocessing on the whole audio file, e.g. click
       removal and silencing gaps, do that next
    7. Run this script. The script will then output two files, labels and tags
    8. Use Audacity's File->Import->"Labels..." option to load the labels file.
    9. Verify that the labels are aligned with the tracks, adjust as needed.
       Note: alt-left and alt-right moves the cursor to the next/prev label.
    10. Using Edit->"Metadata...", load the metadata template XML file that this
       script produced.
    11. Verify that the metadata fields were created as expected.
    12. Proceed with Audacity's File->"Export Multiple...", and you're done.

------------------------------------------------------------------------------ """

from bs4 import BeautifulSoup,NavigableString
from os import listdir,path
from sys import exit
from string import ascii_uppercase

def displayHelpInfo(helpType):
  """ Describe what an information request is seeking in sufficient
  detail for the program user. """
  top = '+--------------------------------------------------+'
  bot = '|--------------------------------------------------|\n' +\
    '| NOTE: See the PDF manual for this app for more   |\n' +\
    '| detailed information.                            |\n' +\
    '+--------------------------------------------------+'
  if helpType == 'selectHtmlFile':
    print(top)
    print('| This application requires an HTML file contain-  |')
    print('| the track list info for the Audacity recording   |')
    print('| to be "ripped" using the Export Multiple feature |')
    print('| of audacity. The HTML files this app uses are    |')
    print('| available from Discogs.com.  If there are no     |')
    print('| HTML files listed above, download the track      |')
    print('| list web page for the album from Discogs and     |')
    print('| re-run this application in the same directory.   |')
    print(bot)
    response = input('Type <Enter> to return or <Q> to quit: ')
    if 'q' == response or 'Q' == response:
      exit(0)
  elif helpType == 'leadInTime':
    print(top)
    print('| The lead-in time is any of the silent part of    |')
    print('| the beginning of the vinyl record (or tape) that |')
    print('| was included in the Audacity recording to be     |')
    print('| "ripped" using Export Multiple.  The default     |')
    print('| value is zero seconds.  Since there is no need   |')
    print('| for this in the recording, it is OK to use the   |')
    print('| delete function in Audacity to remove it.        |')
    print(bot)
    response = input('Type <Enter> to return or <Q> to quit: ')
    if 'q' == response or 'Q' == response:
      exit(0)
  elif helpType == 'trackGapTime':
    print(top)
    print('| The Track Gap Time for an album is the length    |')
    print('| of the silent portion between each track.  This  |')
    print('| is most commonly four seconds but ranges from as |')
    print('| little as zero seconds for some albums to as     |')
    print('| long as eight seconds. (We haven\'t tested every |')
    print('| album so there are probably longer ones).        |')
    print(bot)
    response = input('Type <Enter> to return or <Q> to quit: ')
    if 'q' == response or 'Q' == response:
      exit(0)
  elif helpType == 'approxTimings':
    print(top)
    print('| WARNING: the HTML file that was read for this    |')
    print('| Audacity recording contains no time length info  |')
    print('| for the tracks on the album.  If there are more  |')
    print('| web pages for this album, we recommend downloa-  |')
    print('| ding a web page that shows a track list that     |')
    print('| includes the track time values.                  |')
    print('| As an alternative, this application can provide  |')
    print('| very rough estimates to locate the labels using  |')
    print('| the length of the album divided by the number    |')
    print('| of tracks.  This will require each label after   |')
    print('| the first one to be repositioned manually to the |')
    print('| beginning of each track.                         |')
    print(bot)
    response = input('Type <Enter> to continue with estmated time'+\
       ' or <Q> to quit: ')
    if 'q' == response or 'Q' == response:
      exit(0)
  return


def selectHtmlInputFile():
  """ Get the HTML file containing the album track list """
  haveHtmlFile = False
  filepath = '.'
  while haveHtmlFile == False:
    htmlfilelist = displayHtmlFileList(filepath)
    response = input('\nor Enter Different [P]ath, [H]elp, or [Q]uit: ')
    if 'p' == response or 'P' == response:
      filepath = input('Enter path to search for HTML track list file(s): ')
      if False == path.isdir(filepath):
        print('Unable to find filepath "%s"' % filepath)
        exit(0)
      continue
    if 'h' == response or 'H' == response:
      displayHelpInfo('selectHtmlFile')
      string,response = selectHtmlInputFile()
    if 'q' == response or 'Q' == response:
      exit(0)
    try:
      idx = int(response)
    except ValueError:
      print('Unexpected response received: "%s", exiting.' % (response))
      exit(0)
    # return the HTML file requested by the user
    if idx > len(htmlfilelist) or idx < 0:
      print('ERROR: Your selection "%s" is not a valid file number, exiting.' % response)
      exit(0)
    idx = idx - 1
    print('You responded: %s: "%s"' % (response.upper(),htmlfilelist[idx]))
    return htmlfilelist[idx],response


def determineHtmlPageType(filepath):
  """ Class to help with web page tracklists that use a variation of the
    more common page structure """
  soup = BeautifulSoup (open(filepath), features="lxml")
  tables = soup.find_all('table')
  for table in tables:
    if 'class' in table.attrs:
      tabletype = table['class']
      #print('DBG: Table type "%s" found in "%s"'% (tabletype, filepath))
      return tabletype
  print('ERROR! No track list table found in %s, exiting.'\
    % (filepath))
  exit(-1)


def displayHtmlFileList(filepath):
  """ Read and display a list of HTML files at the specified path. """
  print("\nSelect the name of the html file containing the album track list:\n")
  filelist = listdir(filepath)
  index = 1
  htmlfilelist = []
  for filename in filelist:
    if filename.endswith('.html'):
      print('\t[%d] %s' % (index, filename))
      index += 1
      htmlfilelist.append(path.join(filepath,filename))
  return htmlfilelist


def readAlbumLabelDataFromHtml(filepath, tabletype):
  """ Read the track list table from the HTML file provided """
  soup = BeautifulSoup (open(filepath), features="lxml")
  found_pos = False
  found_time = False
  tracklist = []
  # read the tracklist/playlist table
  table = soup.find('table', {'class': tabletype})
  rows = table.find_all('tr')
  for row in rows:
    track = {}
    # Track position data is in one of two places.  This is the first.
    if 'data-track-position' in row.attrs:
      track['pos'] = row['data-track-position']
      found_pos = True
    cols = row.find_all('td')
    for col in cols:
      spans = col.find_all('span')
      # The track position is in a <td> that has no span
      if len(spans) < 1:
        if 'class' in col.attrs:
          if len(col.text) > 0:
            track['pos'] = col.text
            found_pos = True
      else:
        # The track title is in a span with a class (tracklist_track_title)
        if 'class' in spans[0].attrs:
          track['title'] = spans[0].text
        else: # The track time is in a span with no defined class
          if len(spans[0].text) > 0:
            track['time'] = spans[0].text
            found_time = True
    if len(track['pos']) > 0:
      #print('DBG: found position "%s"...' % (track['pos']))
      tracklist.append(track)
  #print('DBG: Track List:')
  #for track in tracklist:
  #  print('DBG:',track)
  if False == found_time:
    # if there are no track times in the track list, offer to
    #   provide simple approx times (total length/track count).
    tracklist = approxTimings(tracklist)
  return tracklist


def approxTimings(tracklist):
  """ If the user agrees, provide approximate timings using a simple
    calculation based on the number of tracks and the total length of a
    vinyl LP. The user will then need to reposition the labels."""
  totalmin = 0
  displayHelpInfo("approxTimings")
  print('ESTIMATING TRACK LABEL LOCATIONS.')
  response = input('Enter the length of the audacity recording in minutes' + \
    ' (default = 46 minutes): ')
  if response:
    try:
      totalmin = int(response)
    except ValueError:
      print('Unexpected time value received: "%s", exiting.' % (response))
      exit(0)
  if totalmin == 0: # user entered recording length
    totalmin = 46
  totalsecs = totalmin * 60
  tracklen = totalsecs / len(tracklist)
  trackstr = str(int(tracklen/60)) + ':' + str(int(tracklen%60))
  for track in tracklist:
      track['time'] = trackstr
  #print('DBG: approx times total %d tracks' % len(tracklist))
  #print('DBG: Track List:')
  #for track in tracklist:
  #  print('DBG:',track)
  return tracklist


def parseTitleString(pagetitle):
  """ Extract the album name, artist (if present) and year (if present)
    from the page title string. """
  year = 0
  year_found = False
  artist_found = False
  titlestr = pagetitle.split(" | ")[0]
  if titlestr.find(" – ") > 0:
    words = titlestr.split(" – ")
    if words[1] != 'Discogs':
      artist_found = True
  elif titlestr.find(" - ") > 0:
    words = titlestr.split(" - ")
    if words[1] != 'Discogs':
      artist_found = True
  # Compilation album pages do not include the artist in the title.
  if True == artist_found:
    #print('DBG: Artist Found!')
    artist = words[0]
    albumname = words[1]
  else:
    #print('DBG: Artist NOT Found!')
    artist = 'Various'
    albumname = titlestr
  if albumname.find('(') >= 0:
    words2 = albumname.split(" (")
    albumname = words2[0]
  opidx = titlestr.find('(')
  if opidx > 0:
    tempstr = titlestr.split('(')[1]
    comidx = tempstr.find(',')
    if comidx > 0:
      year_cand = tempstr.split(',')[0]
      if len(year_cand) == 4 and True == year_cand.isdigit():
          year = year_cand
          year_found = True
  return(albumname,artist,year,year_found)


def readAlbumTagsDataFromHtml(filepath):
  """ Read the title, artist, genre, and year metadata from the HTML file """
  tagsdict = {}
  soup = BeautifulSoup (open(filepath), features="lxml")
  pagetitle = soup.find('title').text
  # note use of cleanUpString() due to tags used in XML string format
  (album,artist,year,year_found) = parseTitleString(pagetitle)
  tagsdict['ALBUM'] = cleanUpString(album)
  tagsdict['ARTIST'] = cleanUpString(artist)
  if year_found == True:
    tagsdict['YEAR'] = year
  #look for divs containing the remaining album tags,
  #this is a little tricky because the content is in the next
  #div after the one containing the search string.
  all_divs = soup.find_all('div')
  idx = -1
  for div in all_divs:
    idx += 1
    if div.text.endswith(':'):
      label = div.text.strip()
      content = all_divs[idx+1].text.strip()
      if label != content \
        and len(content) > 0 \
        and not (label.lower() == 'year:' and True == year_found)\
        and not (label.lower() == 'released:' and True == year_found)\
        and not (content.find(':') >= 0) \
        and len(label.split()) == 1:
          tagsdict[label[0:-1]] = cleanUpString(content)
  return tagsdict


def getLeadInTime():
  """ Query the user for label positioning info for the
    Audacity recording to be labeled. """
  print(\
    "How much lead-in time before the first track was recorded?")
  response = input('Enter time in seconds, [H]elp, or [Q]uit: [0] ')
  if not response:
    response = '0'
  if 'h' == response or 'H' == response:
    displayHelpInfo('leadInTime')
    response = getLeadInTime()
  if 'q' == response or 'Q' == response:
    exit(0)
  try:
    leadin = int(response)
  except ValueError:
    print('Unexpected response received: "%s", exiting.' % (response))
    exit(0)
  return leadin


def getTrackGapTime():
  """ Query the user for label positioning info for the
    Audacity recording to be labeled. """
  print(\
    "How long is the gap (or silence) between each track?")
  response = input('Enter gap time in seconds, [H]elp, or [Q]uit: [4] ')
  if not response:
    response = '4'
  if 'h' == response or 'H' == response:
    displayHelpInfo('trackGapTime')
    response = getTrackGapTime()
  if 'q' == response or 'Q' == response:
    exit(0)
  try:
    trackgap = int(response)
  except ValueError:
    print('Unexpected response received: "%s", exiting.' % (response))
    exit(0)
  return trackgap


def getSecs(time_str):
    """Return the number of seconds from time string."""
    m, s = time_str.split(':')
    return int(m) * 60 + int(s)


def calculateTiming(leadin,trackgap,tracklist):
  """ Do the number crunching to label each track at the correct
    time in the recording """
  calclist = [] # the track label info list
  totalsecs = 0.0
  trackend = 0.0
  firsttrack = True
  prevtracktime = 0.0
  for track in tracklist:
    labelinf = {}
    if firsttrack == True:
      totalsecs = float(leadin)
      trackend = totalsecs + float(getSecs(track['time']))
      labelinf['duration'] = trackend
      labelinf['time'] = totalsecs
      labelinf['title'] = track['title']
      calclist.append(labelinf)
      prevtracktime = track['time']
      firsttrack = False
    else: # handle all tracks after the first.
      # handle the tracks after the first (trackgap offset)
      totalsecs += getSecs(prevtracktime) + float(trackgap)
      labelinf['time'] = totalsecs
      trackend = totalsecs + float(getSecs(track['time']))
      labelinf['duration'] = trackend
      prevtracktime = track['time']
      labelinf['title'] = track['title']
      calclist.append(labelinf)
  return calclist


def writeLabelFile(labellist, tagsdict):
  """ Write the plaintext labels output file to the current path. """
  filename = (tagsdict['ARTIST']).replace(' ','_') + '-' + \
             (tagsdict['ALBUM']).replace(' ','_') + '-labels.txt'
  response = input('Enter name of label file to write, or [Q]uit: [default="%s"]: ' \
      % filename)
  if response == 'q' or response == 'Q':
    print('[Q]uit requested, exiting...')
    exit(0)
  elif response:
    if response.endswith('.txt'):
      filename = response
    else:
      filename = response + '.txt'
  with open(filename, 'w') as filehandle:
    for label in labellist:
        filehandle.write('%f\t%f\t%s\n' % (label['time'],label['duration'],label['title']))
    filehandle.close()


def buildLabelFile(tracklist,albumname):
  """ Convert the tracklist data to the label file format """
  #print('DBG: track list count = %d' % (len(tracklist)))
  print("\n++++++++++++++++++++++++++++++++++++++++++++++++++++")
  print(  "|     -=> INFORMATION ABOUT THE RECORDING <=-      |")
  print(  "++++++++++++++++++++++++++++++++++++++++++++++++++++")
  print(  "Please provide answers to the following questions about the",\
    "Audacity recording.")
  leadin = getLeadInTime()
  trackgap = getTrackGapTime()
  calclist = calculateTiming(leadin,trackgap,tracklist)
  print('The label list is:\n------------------------------------------')
  for item in calclist:
    print('%f\t%f\t%s' % (item['time'],item['duration'],item['title']))
  print('------------------------------------------')
  return calclist


def writeTagsFile(tagsdict):
  """ Write the XML tags output file to the current path. """
  filename = (tagsdict['ARTIST']).replace(' ','_') + '-' + \
             (tagsdict['ALBUM']).replace(' ','_') + '-tags.xml'
  response = input('Enter name of tags template file to write, or [Q]uit: ["%s"]: ' \
      % filename)
  if response == 'q' or response == 'Q':
    print('[Q]uit requested, exiting...')
    exit(0)
  elif response:
    if response.endswith('.xml'):
      filename = response
    else:
      filename = response + '.xml'
  with open(filename, 'w') as filehandle:
    filehandle.write('<tags>\n')
    for key in tagsdict:
      if key.lower() == 'genre':
        newkey = 'GENRE'
      else:
        newkey = key
      filehandle.write('\t<tag name="' + newkey + '" value="' + \
        (tagsdict[key]).replace('&','&amp;') + '"/>\n')
    filehandle.write('</tags>\n')
    filehandle.close()


def cleanUpString(inputstring):
  """ Remove symbols that don't work well in xml or filename strings """
  outputstring = inputstring.replace('*','').replace('"','').replace('\'','')
  return outputstring


def main():
  """ program main function """
  htmlfile,ignorethis = selectHtmlInputFile()
  pagetype = determineHtmlPageType(htmlfile)
  tracklist = readAlbumLabelDataFromHtml(htmlfile,pagetype)
  tagsdict = readAlbumTagsDataFromHtml(htmlfile)
  labellist = buildLabelFile(tracklist,tagsdict['ALBUM'])
  writeLabelFile(labellist,tagsdict)
  writeTagsFile(tagsdict)
  print('Process completed.')

if __name__ == "__main__":
  main()
