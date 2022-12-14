user_exist = 'username'
pw_exist = 'password'
cwd = '/path/to/src/'
base_url = 'url/to/exist/files'

xslt =  ('''<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:tei="http://www.tei-c.org/ns/1.0">
                <xsl:output method="text" indent="no"/>
                    <!-- Kopfzeile nicht übernehmen -->
                    <xsl:template match="tei:fw"/>
                    <!-- Nur expan übernehmen -->
                    <xsl:template match="tei:abbr"/>
                    <!-- Ausschluss Editorial question -->
                    <xsl:template match="tei:note[@type='editorial-question']">
                    </xsl:template>
                    <!-- Ausschluss Editorial comment -->
                    <xsl:template match="tei:note[@type='editorial-comment']">
                    </xsl:template>
                    <!-- Ausschluss label-->
                    <xsl:template match="tei:label"/>
                    <!-- Ausschluss seg -->
                    <xsl:template match="tei:seg"/>
                    <!-- Ausschluss Interpunktion-->
                    <xsl:template match="tei:pc"/>
                    <!-- Modellierung von Zusätzen -->
                    <!-- Hinzufügungen als '[...]' -->
                    <xsl:template match="tei:add">
                        <xsl:text>[</xsl:text>
                        <xsl:apply-templates/>
                        <xsl:text>]</xsl:text>
                    </xsl:template>
                    <!-- Löschungen als '{...}' -->
                    <xsl:template match="tei:del">
                        <xsl:text>{</xsl:text>
                        <xsl:apply-templates/>
                        <xsl:text>}</xsl:text>
                    </xsl:template>
                    <!-- Löschungen als '{...}' -->
                    <xsl:template match="tei:subst/tei:del"/>
                    <!-- Subst als '{...}' -->
                    <xsl:template match="tei:subst">
                        <xsl:text>{</xsl:text>
                        <xsl:apply-templates/>
                        <xsl:text>}</xsl:text>
                    </xsl:template>
                    <!-- auch mit delSpan... -->
                    <xsl:template match="tei:delSpan">
                        <xsl:text>{</xsl:text>
                    </xsl:template>
                    <!-- ... und dazugehörendem anchor -->
                    <xsl:template match="tei:anchor">
                        <xsl:text>}</xsl:text>
                    </xsl:template>
                    <!-- linebeginnings als einfacher Zeilenumbruch -->
                    <xsl:template match="tei:lb">
                        <xsl:text> </xsl:text>
                    </xsl:template>
                    <!-- lb break ="no" ohne Zeilenumbruch -->
                    <xsl:template match="tei:lb[@break='no']">
                        <xsl:text>+</xsl:text>
                    </xsl:template>
                    <!-- cb ohne Zeilenumbruch -->
                    <xsl:template match="tei:cb"/>
                    <!-- Von oxygen eingefügte Leerzeichenketten in choice entfernen -->
                    <xsl:template match="tei:choice/text()"/>
                    <!-- Von oxygen eingefügte Leerzeichenketten in div entfernen -->
                    <xsl:template match="tei:div/text()"/>
                    <!-- Von oxygen eingefügte Leerzeichenketten in Liste entfernen -->
                    <xsl:template match="tei:list/text()"/>
                    <!-- Von oxygen eingefügte Leerzeichenketten in Liste entfernen -->
                    <xsl:template match="tei:subst/text()"/>
                </xsl:stylesheet>''')

characters_to_normalise = [
                            ['+ ',''],
                            ['+',''],
                            ['_',''],
                            ['ę','e'],
                            ['\n',' '],
                            ['tv','tu'],
                            ['vm','um'],
                            ['vnt','unt'],
                            ['ae','e'],
                            ['vt','ut'],
                            ['rv','ru'],
                            ['coepit','cepit'],
                            ['y','i'],
                            ['cio','tio'],
                            ['cia','tia'],
                            ['mpn','mn'],
                            ['comprou','conprou'],
                            ['ecles','eccles'],
                            ['privetur','priuetur'],
                            ['verum','uerum'],
                            ['repperimus','reperimus'],
                            ['[]',''],
                            [' decimvs ', ' decimus '],
                            [' ieivnio ', ' ieiunio '],
                            [' genva ', ' genua '],
                            [' qvadragesima ', ' quadragesima '],
                            [' tercius ', ' tertius '],
                            [' tercivs ', ' tertius '],
                            [' tertivs ', ' tertius '],
                            [' tercii ', ' tertii '],
                            [' inicium ', ' initium ']
                            #['oe','e'],
                            #[' v ', ' quinque '],
                            #[' iii ', ' tertius '],
                            #[' vi ', ' sex '],
                            #[' xxx ', ' triginta '],
                            #[' xlme ', ' quadragesime '],
                            #[' xlma ', ' quadragesima ']
                            ]