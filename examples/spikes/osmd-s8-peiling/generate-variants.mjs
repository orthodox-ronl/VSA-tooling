/**
 * Schrijf peiling-MusicXML-varianten voor S8-spacers.
 * Geen product-emit — alleen spike-input.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { wrapScore, lyricBlock } from "./_s8-shell.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(__dirname, "variants");

const variants = {
  "01-notehead-none": (text) => `
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>none</stem>
        <notehead>none</notehead>
        ${lyricBlock(text)}
      </note>`,

  "02-print-object-note": (text) => `
      <note print-object="no">
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>none</stem>
        ${lyricBlock(text)}
      </note>`,

  "03-print-object-notehead": (text) => `
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>none</stem>
        <notehead print-object="no">normal</notehead>
        ${lyricBlock(text)}
      </note>`,

  "04-stemless-normal-head": (text) => `
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>none</stem>
        ${lyricBlock(text)}
      </note>`,

  // Structureel: geen pitch-kop — rust als lyric-drager (OSMD-gedrag peilen).
  "05-rest-with-lyric": (text) => `
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
        ${lyricBlock(text)}
      </note>`,
};

fs.mkdirSync(outDir, { recursive: true });
for (const [name, spacerFn] of Object.entries(variants)) {
  const xml = wrapScore(spacerFn);
  const dest = path.join(outDir, `${name}.musicxml`);
  fs.writeFileSync(dest, xml, "utf8");
  console.log("wrote", path.relative(process.cwd(), dest));
}
