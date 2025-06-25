require "isodoc"
require "isodoc/html_convert"   # 🔥 이거 반드시 추가!
require "isodoc/generic/html_convert"
require_relative "init"

module IsoDoc
  module Iho
    class HtmlConvert < IsoDoc::Generic::HtmlConvert
      include BaseConvert
      include Init

      # 🔥 기존 generic 설정 무시하고 scripts.html만 로딩
      def default_file_locations(_options)
 	 super.merge(
   	 scripts: File.join(File.dirname(__FILE__), "html", "scripts.html")
 	 )
	end
    end
  end
end

