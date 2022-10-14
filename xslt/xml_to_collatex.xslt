<!-- bereitet XML für Collation in collatex vor --><xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema" version="2.0" xpath-default-namespace="http://www.tei-c.org/ns/1.0" exclude-result-prefixes="xs">
    <xsl:output method="text" indent="no"/>

    <xsl:template match="/">
        <xsl:apply-templates/>
    </xsl:template>

    <!-- nur Kindelemente von 'body' auswerten -->
    <xsl:template match="TEI">
        <xsl:apply-templates select="text/body/*"/>
    </xsl:template>

    <!-- nur Kindelemente von TOC auswerten
    <xsl:template match="TEI">
        <xsl:apply-templates select="text/body//list/*"/>
    </xsl:template>  -->

    <!-- nur Kindelemente von content auswerten
    <xsl:template match="TEI">
        <xsl:apply-templates select="text/body//div[@type='content']/*"/>
    </xsl:template> -->

    <!-- ggf. Textbegrenzung für Collatex markieren durch inter -->
    <xsl:template match="interp">
        <xsl:text>collatex:</xsl:text><xsl:value-of select="./@ana"/><xsl:text> </xsl:text>
    </xsl:template>

    <!-- Kopfzeile nicht übernehmen -->
    <xsl:template match="fw"/>


    <!-- Nur expan übernehmen -->
    <xsl:template match="abbr"/>

    <!-- Elemente, die in Kollation nicht berücksichtig werden -->
    <!-- Ausschluss Tabelle -->
    <xsl:template match="table">
    </xsl:template>

    <!-- Ausschluss Editorial question -->
    <xsl:template match="note[@type='editorial-question']">
    </xsl:template>

    <!-- Ausschluss Editorial comment -->
    <xsl:template match="note[@type='editorial-comment']">
    </xsl:template>

    <!-- Ausschluss Inskription -->
    <xsl:template match="note[@type='inscription']">
    </xsl:template>

    <!-- Ausschluss label-->
    <xsl:template match="label"/>


    <!-- Ausschluss seg -->
    <xsl:template match="seg"/>

    <!-- supplied ohne Leerzeichen -->
    <xsl:template match="supplied">
        <xsl:text>_</xsl:text><xsl:apply-templates/>
    </xsl:template>



    <!-- Ausschluss Interpunktion-->
    <xsl:template match="pc"/>


    <!-- Modellierung von Zusätzen -->

    <!-- Hinzufügungen als '[...]' -->
    <xsl:template match="add">
        <xsl:text>[</xsl:text>
        <xsl:apply-templates/>
        <xsl:text>]</xsl:text>
    </xsl:template>


    <!-- Löschungen als '{...}' -->
    <xsl:template match="del">
        <xsl:text>{</xsl:text>
        <xsl:apply-templates/>
        <xsl:text>}</xsl:text>
    </xsl:template>

    <!-- Löschungen als '{...}' -->
    <xsl:template match="subst/del"/>

    <!-- Subst als '{...}' -->
    <xsl:template match="subst">
        <xsl:text>{</xsl:text>
        <xsl:apply-templates/>
        <xsl:text>}</xsl:text>
    </xsl:template>

    <!-- auch mit delSpan... -->
    <xsl:template match="delSpan">
        <xsl:text>{</xsl:text>
    </xsl:template>

    <!-- ... und dazugehörendem anchor -->
    <xsl:template match="anchor">
        <xsl:text>}</xsl:text>
    </xsl:template>


    <!-- Nach div="chapter" Zeilenumbruch -->

    <!-- Divs als NL und Divnumber -->
    <xsl:template match="div[@type='chapter']">
        <xsl:text>K</xsl:text><xsl:value-of select="./@n"/><xsl:text>
</xsl:text>
        <xsl:apply-templates/>
        <xsl:text>

</xsl:text>
    </xsl:template>

    <!-- Nach item Zeilenumbruch -->

    <!-- item als NL und itemnumber -->
    <xsl:template match="item">
        <xsl:text>TOC</xsl:text><xsl:value-of select="./@n"/><xsl:text>
</xsl:text>
        <xsl:apply-templates/>
        <xsl:text>

</xsl:text>
    </xsl:template>



    <!-- linebeginnings als einfacher Zeilenumbruch -->
    <xsl:template match="lb">
        <xsl:text> </xsl:text>
    </xsl:template>

    <!-- lb break ="no" ohne Zeilenumbruch -->
    <xsl:template match="lb[@break='no']">
        <xsl:text>+</xsl:text>
    </xsl:template>

    <!-- cb ohne Zeilenumbruch -->
    <xsl:template match="cb"/>

    <!-- Leerzeichen -->
    <!-- Leerzeichen normalisieren -->
    <xsl:template match="text()">
        <xsl:analyze-string select="." regex="\s+">
            <xsl:matching-substring><xsl:text> </xsl:text></xsl:matching-substring>
            <xsl:non-matching-substring><xsl:value-of select="."/></xsl:non-matching-substring>
        </xsl:analyze-string>
    </xsl:template>

    <!-- Newlines normalisieren  -->
    <xsl:template match="text()">
        <xsl:analyze-string select="." regex="\n">
            <xsl:matching-substring><xsl:text/></xsl:matching-substring>
            <xsl:non-matching-substring><xsl:value-of select="."/></xsl:non-matching-substring>
        </xsl:analyze-string>
    </xsl:template>


    <!-- Von oxygen eingefügte Leerzeichenketten in choice entfernen -->
    <xsl:template match="choice/text()"/>

    <!-- Von oxygen eingefügte Leerzeichenketten in div entfernen -->
    <xsl:template match="div/text()"/>

    <!-- Von oxygen eingefügte Leerzeichenketten in Liste entfernen -->
    <xsl:template match="list/text()"/>

    <!-- Von oxygen eingefügte Leerzeichenketten in Liste entfernen -->
    <xsl:template match="subst/text()"/>

    <!-- Leerzeichen  nach Satzzeichen sicherstellen -->
    <!--    <xsl:template match="pc">
        <xsl:apply-templates/>
        <xsl:text> </xsl:text>
    </xsl:template>-->

    <!-- Leerzeichen vor und nach choice sicherstellen bzw. ausschließen  -->
    <!-- besser mit <xsl:value-of select="."/>-->
    <!-- funktioniert nicht wenn normales Wort vor abbr kommt -->

    <!--    <xsl:template match="abbr">
        <xsl:choose>
            <xsl:when test="preceding::*[1][self::lb]"></xsl:when>
            <xsl:when test="preceding::*[2][self::pc]"></xsl:when>
            <xsl:otherwise>
                <xsl:text> </xsl:text>
            </xsl:otherwise>
        </xsl:choose>

        <xsl:apply-templates/>

        <xsl:choose>
            <xsl:when test="following::*[2][self::pc]"></xsl:when>
            <xsl:when test="following::*[2][self::abbr]"></xsl:when>
            <xsl:otherwise>
                <xsl:text> </xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
-->


</xsl:stylesheet>
