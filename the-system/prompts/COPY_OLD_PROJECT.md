NOTE: Assume the-system directory is already copied to this new project and we are running this from the new project's directory.

Old Project Location: ../AlfConn/

Please read @the-system\HOW_THIS_WORKS.md .

I want to rewrite the old project from scratch here in this new project. All I really need is a good ./README.md file and likely several ./readme/ markdown documents.

Notice that the old project has .md files under ..\AlfConn\doc\per-soap-method\ directory, e.g. ..\AlfConn\doc\per-soap-method\Crawl2\Crawl2.md ; each of these .md files should become one .md file under ./readme/ directory, but it should be rewritten to better match this type of project.

See the README.md file in the old project, and the SPECIFICATION.md file in the old project. We will not be using the same methods for software construction; instead we will use our own @the-system\HOW_THIS_WORKS.md . BUT we will be keeping the same goals and the same ./release/ files (i.e. )


now: suggest a design where response headers are modified to exactly match the legacy headers, but bodies will be not be modified.


later: make log formats the same
later: make sure alfresco REST API calls match those in the trace logs
later: write a test that matches every request to every response in the network trace
