/**
 * Shared MusicXML shell for S8 spacer peiling (one staff, senza misura).
 * Pattern: Al (quarter) | le (breveHead) | lu i a (spacers) | al (quarter).
 * Spacer body is injected per variant.
 */

export function wrapScore(spacerNoteXml) {
  // spacerNoteXml: function(lyric) => MusicXML <note>…</note> for one spacer
  const spacers = ["lu", "i", "a"].map(spacerNoteXml).join("\n");
  return `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC
  "-//Recordare//DTD MusicXML 3.1 Partwise//EN"
  "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1"><part-name></part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>4</divisions>
        <key><fifths>0</fifths></key>
        <time><senza-misura/></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><syllabic>begin</syllabic><text>Al</text></lyric>
      </note>
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>none</stem>
        <notehead>breve</notehead>
        <lyric number="1"><syllabic>middle</syllabic><text>le</text></lyric>
      </note>
${spacers}
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><syllabic>end</syllabic><text>al</text></lyric>
      </note>
      <barline location="right"><bar-style>light-heavy</bar-style></barline>
    </measure>
  </part>
</score-partwise>
`;
}

export function lyricBlock(text, syllabic = "middle") {
  return `<lyric number="1"><syllabic>${syllabic}</syllabic><text>${text}</text></lyric>`;
}
